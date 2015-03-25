from collections import namedtuple

from pyquery import PyQuery

from ._compat import string_types, StringIO
from .scanner import Scanner, TokenType


class AlreadyParsedError(Exception):
    pass

class UnexpectedEOFError(Exception):
    pass

class UnexpectedTokenError(Exception):
    def __init__(self, found, expected, msg=None, token=None):
        self.found = found
        self.expected = expected
        self.msg = msg
        self.token = token

    def __str__(self):
        return ('UnexpectedTokenError {{\n'
                '       found: {!r}\n'
                '    expected: {!r}\n'
                '         msg: {!r}\n'
                '       token: {}\n'
                '}}').format(self.found, self.expected, self.msg, self.token)

class InvalidDirectiveError(Exception):
    def __init__(self, ident, msg=None):
        self.ident = ident
        self.msg = msg

    def __str__(self):
        return ('InvalidDirectiveError {{\n'
                '      ident: {!r}\n'
                '    message: {!r}\n'
                '}}').format(self.ident, self.message)

class TakeSyntaxError(Exception):
    def __init__(self, msg, extra=None):
        self.msg = msg
        self.extra = extra

    def __str__(self):
        return ('TakeSyntaxError {{\n'
                '      message: {!r}\n'
                '        extra: {!r}\n'
                '}}').format(self.message, self.extra)


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

def make_text_query():
    return lambda elm: ensure_pq(elm).text()

def make_attr_query(attr):
    return lambda elm: ensure_pq(elm).attr(attr)

def parse_save_to_id(tok):
    if tok.type_ != TokenType.DirectiveBodyItem:
        raise UnexpectedTokenError(tok.type_, TokenType.DirectiveBodyItem)
    save_to = tok.content.strip()
    if '.' in save_to:
        return tuple(save_to.split('.'))
    else:
        return (save_to,)

def save_to(dest, name_parts, value):
    """
    Util to save some name sequence to a dict. For instance, `("location","query")` would save
    to dest["location"]["query"].
    """
    if len(name_parts) > 1:
        for part in name_parts[:-1]:
            if part not in dest:
                dest[part] = {}
            dest = dest[part]
    dest[name_parts[-1]] = value


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
        if last_value != None:
            self.last_value = last_value
        elif value != None:
            self.last_value = value
        elif context:
            if context.last_value != None:
                self.last_value = context.last_value
            elif context.value != None:
                self.last_value = context.value
            else:
                self.last_value = None
        else:
            self.last_value = None
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


class SaveNode(namedtuple('SaveNode', 'ident_parts')):
    __slots__ = ()
    def do(self, context):
        save_to(context.rv, self.ident_parts, context.value)


class SaveEachNode(namedtuple('SaveEachNode', 'ident_parts sub_ctx_node')):
    __slots__ = ()
    def do(self, context):
        results = []
        save_to(context.rv, self.ident_parts, results)
        for item in context.value:
            rv = {}
            results.append(rv)
            self.sub_ctx_node.do(None, rv, item, item)


class ContextParser(object):

    def __init__(self, depth, tok_gen):
        self._depth = depth
        self._tok_generator = tok_gen
        self._nodes = None
        self._tok = None
        self._is_done = False

    def destroy(self):
        self._depth = None
        self._tok_generator = None
        self._nodes = None
        self._tok = None
        self._is_done = None


    def parse(self):
        if self._is_done:
            raise AlreadyParsedError
        self._nodes = []
        tok = self._parse()
        return ContextNode(self._depth, self._nodes), tok


    def _next_tok(self, eof_errors=True):
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
            tok = self._next_tok()
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
                tok = self._next_tok(eof_errors=False)
            if self._is_done:
                # returning None means EOF ended this context, not a context exit
                return
            if tok.type_ != TokenType.Context:
                raise UnexpectedTokenError(self._tok.type_, TokenType.Context, token=tok)
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
            # context token same depth as this context, so continue parsing

    def _parse_context(self):
        sub_ctx = ContextParser(self._tok.end, self._tok_generator)
        sub_ctx_node, tok = sub_ctx.parse()
        self._nodes.append(sub_ctx_node)
        sub_ctx.destroy()
        return tok

    def _parse_query(self):
        self._next_tok()
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
        self._next_tok()
        if self._tok.type_ == TokenType.QueryStatementEnd:
            return (query,)
        elif self._tok.type_ == TokenType.AccessorSequence:
            return (query,) + self._parse_accessor_seq()
        else:
            raise UnexpectedTokenError(self._tok.type_, (TokenType.QueryStatementEnd,
                                                         TokenType.AccessorSequence))

    def _parse_accessor_seq(self):
        queries = ()
        tok = self._next_tok()
        # index accessor has to be first
        if tok.type_ == TokenType.IndexAccessor:
            index_str = tok.content
            queries = (make_index_query(index_str),)
            tok = self._next_tok()
            # index accessor can be the only accessor
            if tok.type_ == TokenType.QueryStatementEnd:
                return queries
        if tok.type_ == TokenType.TextAccessor:
            queries += (make_text_query(),)
        elif tok.type_ == TokenType.AttrAccessor:
            # strip spaces and remove the brackets
            # ex: [src]
            attr = tok.content.strip()[1:-1]
            queries += (make_attr_query(attr),)
        else:
            # if it got here, something is wrong, should either have exited after the index
            # accessor (if there was one) or there should have been a text or attr accessor
            expected = (TokenType.TextAccessor, TokenType.AttrAccessor)
            if not queries:
                expected += (TokenType.IndexAccessor,)
            raise UnexpectedTokenError(tok.type_, expected, token=tok)
        # can only have one of text accessor or attr accessor, so do not need to loop
        tok = self._next_tok()
        if tok.type_ != TokenType.QueryStatementEnd:
            raise UnexpectedTokenError(tok.type_, TokenType.QueryStatementEnd, token=tok)
        return queries

    def _parse_directive(self):
        tok = self._next_tok()
        if tok.type_ != TokenType.DirectiveIdentifier:
            raise UnexpectedTokenError(tok.type_, TokenType.DirectiveIdentifier, token=tok)
        dir_ident = tok.content.strip()
        if dir_ident == 'save':
            return self._parse_save_directive()
        elif dir_ident == 'save each':
            return self._parse_save_each_directive()
        else:
            raise InvalidDirectiveError(dir_ident, 'Unknown directive, valid directives: %r' %
                                                   ['save', 'save each'])

    def _parse_save_directive(self):
        tok = self._next_tok()
        save_id_parts = parse_save_to_id(tok)
        node = SaveNode(save_id_parts)
        self._nodes.append(node)

    def _parse_save_each_directive(self):
        tok = self._next_tok()
        save_id_parts = parse_save_to_id(tok)
        # consume the context token and parse the sub-context SaveEachNode will manage
        tok = self._next_tok()
        if tok.type_ != TokenType.Context:
            raise UnexpectedTokenError(tok.type_, TokenType.Context, token=tok)
        if tok.end <= self._depth:
            raise TakeSyntaxError('Invalid depth, expecting to start a "save each" context.', extra=tok)
        sub_ctx = ContextParser(tok.end, self._tok_generator)
        sub_ctx_node, tok = sub_ctx.parse()
        sub_ctx.destroy()
        node = SaveEachNode(save_id_parts, sub_ctx_node)
        self._nodes.append(node)
        return tok


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
