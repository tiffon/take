from collections import namedtuple, MutableMapping
from itertools import chain
import sys

from pyquery import PyQuery

from ._compat import string_types, StringIO
from .directives import BUILTIN_DIRECTIVES
from .exceptions import AlreadyParsedError, UnexpectedEOFError, \
     UnexpectedTokenError, InvalidDirectiveError, TakeSyntaxError
from .scanner import Scanner, TokenType
from .utils import split_name, get_via_name_list


_BUILTIN_DIRECTIVES_IDS = set(BUILTIN_DIRECTIVES.keys())


def ensure_pq(elm):
    if isinstance(elm, PyQuery):
        return elm
    else:
        return PyQuery(elm)


def make_css_query(selector):
    return lambda elm: ensure_pq(elm)(selector)


def make_index_query(index_str):
    index = int(index_str)
    if index > -1:
        return lambda elm: ensure_pq(elm).eq(index)
    # PyQuery doesn't handle negative indexes, so calc the real index each time
    def index_query(elm):
        elm = ensure_pq(elm)
        i = len(elm) + index
        return elm.eq(i)
    return index_query


def text_query(elm):
    return ensure_pq(elm).text()


def own_text_query(elm):
    return ''.join(item
                   for item in ensure_pq(elm).contents()
                   if isinstance(item, string_types))


def make_attr_query(attr):
    return lambda elm: ensure_pq(elm).attr(attr)


def make_field_query(name):
    name_list = split_name(name)
    return lambda source: get_via_name_list(source, name_list)


class ContextNode(object):
    __slots__ = ('__depth', '__nodes', '__rv', '__value', 'last_value')

    def __init__(self, depth, nodes):
        self.__depth = depth
        self.__nodes = nodes
        self.__rv = None
        self.__value = None
        self.last_value = None

    @property
    def rv(self):
        return self.__rv

    @property
    def value(self):
        return self.__value

    def do(self, context, rv=None, value=None, last_value=None):
        self.__rv = rv if rv != None else context.rv
        # value in a sub-context is derived from the last_value in the parent context
        self.__value = value if value != None else context.last_value
        self.last_value = last_value if last_value != None else self.__value
        for node in self.__nodes:
            node.do(self)


class QueryNode(namedtuple('QueryNode', 'queries')):
    __slots__ = ()
    def do(self, context):
        # start last_value based on context.value
        val = context.value
        # queries can be a sequence of queries
        for query in self.queries:
            val = query(val)
        # update context.last_value
        context.last_value = val


class ChainedMapping(MutableMapping):
    """
    A dictionary that looks for a specific key and if it's not present looks for
    it on it's parent
    """

    def __init__(self, parent=None, *args, **kwargs):
        self.parent = parent or {}
        self.store = {}
        if args:
            self.update(*args)
        if kwargs:
            self.update(**kwargs)

    def __getitem__(self, key):
        if key in self.store:
            return self.store[key]
        return self.parent[key]

    def __setitem__(self, key, value):
        self.store[key] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return chain(iter(self.store), iter(self.parent))

    def __len__(self):
        return len(self.store) + len(self.parent)

    def make_child(self, *args, **kwargs):
        return ChainedMapping(self, *args, **kwargs)

    def destroy(self, *args, **kwargs):
        self.parent = None
        self.store = None


class ContextParser(object):

    def __init__(self, depth, tok_gen, defs=None, from_inline=False):
        self._depth = depth
        self._tok_generator = tok_gen
        self._defs = defs or ChainedMapping()
        self._from_inline = from_inline
        self._nodes = None
        self._tok = None
        self._is_done = False

    @property
    def depth(self):
        return self._depth

    @property
    def defs(self):
        return self._defs

    @property
    def tok(self):
        return self._tok

    def destroy(self):
        self._depth = None
        self._tok_generator = None
        self._defs.destroy()
        self._defs = None
        self._nodes = None
        self._tok = None
        self._is_done = None


    def parse(self):
        if self._is_done:
            raise AlreadyParsedError
        self._nodes = []
        tok = self._parse()
        return ContextNode(self._depth, self._nodes), tok


    def spawn_context_parser(self, depth=None, from_inline=False):
        if depth == None:
            depth = self._tok.end
        defs = self._defs.make_child()
        return ContextParser(depth, self._tok_generator, defs, from_inline)


    def next_tok(self, eof_errors=True):
        try:
            self._tok = next(self._tok_generator)
            return self._tok
        except StopIteration:
            self._tok = None
            self._is_done = True
            if eof_errors:
                raise UnexpectedEOFError

    def _parse(self):
        while True:
            tok = self.next_tok()
            if tok.type_ == TokenType.QueryStatement:
                self._parse_query()
                tok = None
            elif tok.type_ == TokenType.DirectiveStatement:
                # some directives consume a context token to determine if they end (eg SaveEachNode)
                tok = self._parse_directive()
            else:
                raise UnexpectedTokenError(tok.type_,
                                          (TokenType.QueryStatement, TokenType.DirectiveStatement),
                                          token=tok)
            if not tok:
                tok = self.next_tok(eof_errors=False)
            if self._is_done:
                # returning None means EOF ended this context, not a context exit
                return
            if tok.type_ not in (TokenType.Context, TokenType.InlineSubContext):
                raise UnexpectedTokenError(self._tok.type_,
                                           (TokenType.Context, TokenType.InlineSubContext),
                                           token=tok)
            if tok.type_ == TokenType.InlineSubContext:
                end_tok = self._parse_inline_context()
                if not end_tok:
                    # reached EOF
                    return
                else:
                    # should be a context token
                    if end_tok.type_ != TokenType.Context:
                        raise UnexpectedTokenError(self._tok.type_, TokenType.Context, token=tok)
                    # end_tok should be treated like any other context token, either indicates a
                    # sub-context, releases to the parent context or continues in this context
                    tok = end_tok
            if tok.end > self._depth:
                end_tok = self._parse_context()
                if not end_tok:
                    # end_tok is either the last token grabbed by the sub-context or None, if it is
                    # None, then we have reached EOF
                    return
                else:
                    # if end_tok a token, it is a context token and is less than the sub-context,
                    # possibly less the current context... use it as the context node to check to
                    # see if this context should end
                    tok = end_tok
                # TODO(joe): consider checking for bug/bad contexts in the source where enter the
                # sub-context with indent+4 but exit with indent+2, so, exit the sub-context but
                # would be in another sub-context (prob should not allow)
            if tok.end < self._depth:
                return tok
            # context token is the same depth as the current context parser
            # exit if the current context parse was created from an inline context
            # (they only persist when the context token is deeper)
            if self._from_inline:
                return tok

    def _parse_context(self):
        sub_ctx = self.spawn_context_parser()
        sub_ctx_node, tok = sub_ctx.parse()
        self._nodes.append(sub_ctx_node)
        sub_ctx.destroy()
        return tok

    def _parse_inline_context(self):
        sub_ctx = self.spawn_context_parser(self._depth, True)
        sub_ctx_node, tok = sub_ctx.parse()
        self._nodes.append(sub_ctx_node)
        sub_ctx.destroy()
        return tok

    def _parse_query(self):
        self.next_tok()
        if self._tok.type_ == TokenType.CSSSelector:
            queries = self._parse_css_selector()
        elif self._tok.type_ == TokenType.AccessorSequence:
            queries = self._parse_accessor_seq()
        else:
            raise UnexpectedTokenError(self._tok.type_, (TokenType.CSSSelector,
                                                         TokenType.AccessorSequence))
        node = QueryNode(queries)
        self._nodes.append(node)

    def _parse_css_selector(self):
        selector = self._tok.content.strip()
        # expects a valid css selector
        query = make_css_query(selector)
        self.next_tok()
        if self._tok.type_ == TokenType.QueryStatementEnd:
            return (query,)
        elif self._tok.type_ == TokenType.AccessorSequence:
            return (query,) + self._parse_accessor_seq()
        else:
            raise UnexpectedTokenError(self._tok.type_, (TokenType.QueryStatementEnd,
                                                         TokenType.AccessorSequence))

    def _parse_accessor_seq(self):
        queries = ()
        tok = self.next_tok()
        # index accessor has to be first
        if tok.type_ == TokenType.IndexAccessor:
            index_str = tok.content
            queries = (make_index_query(index_str),)
            tok = self.next_tok()
            # index accessor can be the only accessor
            if tok.type_ == TokenType.QueryStatementEnd:
                return queries
        # text accessor
        if tok.type_ == TokenType.TextAccessor:
            queries += (text_query,)
        # own text accessor
        elif tok.type_ == TokenType.OwnTextAccessor:
            queries += (own_text_query,)
        # attr accessor
        elif tok.type_ == TokenType.AttrAccessor:
            # strip spaces and remove the brackets
            # ex: [src]
            attr = tok.content.strip()[1:-1]
            queries += (make_attr_query(attr),)
        # field accessor
        elif tok.type_ == TokenType.FieldAccessor:
            # strip spaces and remove the dot
            # ex: '".field_name"'
            field = tok.content.strip()[1:]
            queries += (make_field_query(field),)
        # invalid
        else:
            # if it got here, something is wrong, should either have exited after the index
            # accessor (if there was one) or there should have been a text or attr accessor
            expected = (
                TokenType.TextAccessor,
                TokenType.OwnTextAccessor,
                TokenType.AttrAccessor,
                TokenType.FieldAccessor,
            )
            if not queries:
                expected += (TokenType.IndexAccessor,)
            raise UnexpectedTokenError(tok.type_, expected, token=tok)
        # can only have one of text accessor or attr accessor, so do not need to loop
        tok = self.next_tok()
        if tok.type_ != TokenType.QueryStatementEnd:
            raise UnexpectedTokenError(tok.type_, TokenType.QueryStatementEnd, token=tok)
        return queries

    def _parse_directive(self):
        tok = self.next_tok()
        if tok.type_ != TokenType.DirectiveIdentifier:
            raise UnexpectedTokenError(tok.type_, TokenType.DirectiveIdentifier, token=tok)
        name = tok.content.strip()
        if name in BUILTIN_DIRECTIVES:
            end_tok, node = BUILTIN_DIRECTIVES[name](self)
            if node != None:
                # node is `None` for `def:` subroutines
                self._nodes.append(node)
            return end_tok
        def_node = self._defs.get(name)
        if def_node:
            self._parse_call_user_subroutine(def_node)
        else:
            raise InvalidDirectiveError(name, 'Unknown directive: %s' % name)

    def _parse_call_user_subroutine(self, def_node):
        # calling a subroutine
        self._nodes.append(def_node)
        tok = self.next_tok()
        if tok.type_ != TokenType.DirectiveStatementEnd:
            raise UnexpectedTokenError(tok.type_, TokenType.DirectiveStatementEnd, token=tok)


def parse(src):
    if isinstance(src, string_types):
        fobj = StringIO(src)
    else:
        fobj = src
    scanner = Scanner(fobj)
    tok_generator = scanner.scan()
    tok = next(tok_generator)
    if tok.type_ != TokenType.Context:
        raise UnexpectedTokenError(tok.type_, TokenType.Context, 'Leading context token not found')
    ctx_parser = ContextParser(tok.end, tok_generator)
    node, last_tok = ctx_parser.parse()
    ctx_parser.destroy()
    if last_tok:
        raise UnexpectedTokenError(last_tok, 'EOF')
    return node
