from collections import namedtuple
import re

from ._compat import string_types
from .exceptions import UnexpectedTokenError, TakeSyntaxError
from .scanner import TokenType
from .utils import split_name, get_via_name_list, save_to_name_list


_WS = re.compile(r'\s+')


class _SaveNode(namedtuple('_SaveNode', 'ident_parts')):
    __slots__ = ()
    def do(self, context):
        save_to_name_list(context.rv, self.ident_parts, context.value)


def make_save(parser):
    tok = parser.next_tok()
    if tok.type_ != TokenType.DirectiveBodyItem:
        raise UnexpectedTokenError(tok.type_, TokenType.DirectiveBodyItem)
    save_id_parts = split_name(tok.content.strip())
    tok = parser.next_tok()
    # expecting only have one parameter
    if tok.type_ != TokenType.DirectiveStatementEnd:
        raise UnexpectedTokenError(tok.type_, TokenType.DirectiveStatementEnd, token=tok)
    return None, _SaveNode(save_id_parts)


class _SaveEachNode(namedtuple('_SaveEachNode', 'ident_parts sub_ctx_node')):
    __slots__ = ()
    def do(self, context):
        results = []
        save_to_name_list(context.rv, self.ident_parts, results)
        for item in context.value:
            rv = {}
            results.append(rv)
            self.sub_ctx_node.do(None, rv, item, item)


def make_save_each(parser):
    tok = parser.next_tok()
    if tok.type_ != TokenType.DirectiveBodyItem:
        raise UnexpectedTokenError(tok.type_, TokenType.DirectiveBodyItem)
    save_id_parts = split_name(tok.content.strip())
    tok = parser.next_tok()
    # expecting only have one parameter
    if tok.type_ != TokenType.DirectiveStatementEnd:
        raise UnexpectedTokenError(tok.type_, TokenType.DirectiveStatementEnd, token=tok)
    # consume the context token which should be a sub-context
    tok = parser.next_tok()
    if tok.type_ != TokenType.Context:
        raise UnexpectedTokenError(tok.type_, TokenType.Context, token=tok)
    if tok.end <= parser.depth:
        raise TakeSyntaxError('Invalid depth, expecting to start a "save each" context.',
                              extra=tok)
    #  parse the sub-context SaveEachNode will manage
    sub_ctx = parser.spawn_context_parser()
    sub_ctx_node, tok = sub_ctx.parse()
    sub_ctx.destroy()
    return tok, _SaveEachNode(save_id_parts, sub_ctx_node)


class _NamespaceNode(namedtuple('_NamespaceNode', 'ident_parts sub_ctx_node')):
    __slots__ = ()
    def do(self, context):
        # re-use the namespace if it was already defined ealier in the doc
        sub_rv = get_via_name_list(context.rv, self.ident_parts)
        if not sub_rv:
            sub_rv = {}
        save_to_name_list(context.rv, self.ident_parts, sub_rv)
        self.sub_ctx_node.do(None, sub_rv, context.value, context.value)


def make_namespace(parser):
    tok = parser.next_tok()
    if tok.type_ != TokenType.DirectiveBodyItem:
        raise UnexpectedTokenError(tok.type_, TokenType.DirectiveBodyItem)
    save_id_parts = split_name(tok.content.strip())
    tok = parser.next_tok()
    # expecting only have one parameter
    if tok.type_ != TokenType.DirectiveStatementEnd:
        raise UnexpectedTokenError(tok.type_, TokenType.DirectiveStatementEnd, token=tok)
    # consume the context token which should be a sub-context
    tok = parser.next_tok()
    if tok.type_ != TokenType.Context:
        raise UnexpectedTokenError(tok.type_, TokenType.Context, token=tok)
    if tok.end <= parser.depth:
        raise TakeSyntaxError('Invalid depth, expecting to start a "namespace" context.',
                              extra=tok)
    #  parse the sub-context _NamespaceNode will manage
    sub_ctx = parser.spawn_context_parser()
    sub_ctx_node, tok = sub_ctx.parse()
    sub_ctx.destroy()
    return tok, _NamespaceNode(save_id_parts, sub_ctx_node)


class _DefSubroutine(namedtuple('_DefSubroutine', 'sub_ctx_node')):
    __slots__ = ()
    def do(self, context):
        rv = {}
        self.sub_ctx_node.do(None, rv, context.value, context.value)
        context.last_value = rv


def make_def_subroutine(parser):
    name_parts = []
    tok = parser.next_tok()
    # can have more than one name to merge
    while tok.type_ == TokenType.DirectiveBodyItem:
        name_parts.append(tok.content.strip())
        tok = parser.next_tok()
    if not name_parts:
        raise TakeSyntaxError('The def directive requires a parameter.', tok)
    def_name = ' '.join(name_parts)
    if tok.type_ != TokenType.DirectiveStatementEnd:
        raise UnexpectedTokenError(tok.type_, TokenType.DirectiveStatementEnd, token=tok)
    # consume the context token which should be a sub-context
    tok = parser.next_tok()
    if tok.type_ != TokenType.Context:
        raise UnexpectedTokenError(tok.type_, TokenType.Context, token=tok)
    if tok.end <= parser.depth:
        raise TakeSyntaxError('Invalid depth, expecting to start a "def" subroutine context.',
                              extra=tok)
    #  parse the sub-context _DefSubroutine will manage
    sub_ctx = parser.spawn_context_parser()
    sub_ctx_node, tok = sub_ctx.parse()
    sub_ctx.destroy()
    subroutine = _DefSubroutine(sub_ctx_node)
    parser.defs[def_name] = subroutine
    return tok, None


class _MergeNode(namedtuple('_MergeNode', 'names_to_save save_all')):
    __slots__ = ()
    def do(self, context):
        if self.save_all:
            # do a shallow merge
            context.rv.update(context.value)
        else:
            src = context.value
            dest = context.rv
            for name_parts in self.names_to_save:
                val = get_via_name_list(src, name_parts)
                save_to_name_list(dest, name_parts, val)


def make_merge(parser):
    names_to_save = []
    tok = parser.next_tok()
    # can have more than one name to merge
    while tok.type_ == TokenType.DirectiveBodyItem:
        id_parts = split_name(tok.content.strip())
        names_to_save.append(id_parts)
        tok = parser.next_tok()
    if not names_to_save:
        raise TakeSyntaxError('The merge directive requires a parameter, "*" '
                              'to save all list of keys',
                              tok)
    if tok.type_ != TokenType.DirectiveStatementEnd:
        raise UnexpectedTokenError(tok.type_, TokenType.DirectiveStatementEnd, token=tok)
    if names_to_save == [('*',)]:
        all = True
        names_to_save = None
    else:
        all = False
        names_to_save = tuple(names_to_save)
    return None, _MergeNode(names_to_save, all)


class _ShrinkNode(object):
    __slots__ = ()
    def do(self, context):
        val = context.value
        if not isinstance(val, string_types):
            tx = val.text()
        else:
            tx = val
        context.last_value = _WS.sub(' ', tx.strip())


def make_shrink(parser):
    tok = parser.next_tok()
    # shouldn't have any parameters
    if tok.type_ != TokenType.DirectiveStatementEnd:
        raise UnexpectedTokenError(tok.type_, TokenType.DirectiveStatementEnd, token=tok)
    return None, _ShrinkNode()


BUILTIN_DIRECTIVES = {
    'save':         make_save,
    ':':            make_save,
    'save each':    make_save_each,
    'namespace':    make_namespace,
    '+':            make_namespace,
    'def':          make_def_subroutine,
    'merge':        make_merge,
    '>>':           make_merge,
    'shrink':       make_shrink,
}
