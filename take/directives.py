from collections import namedtuple

from .exceptions import UnexpectedTokenError, TakeSyntaxError
from .scanner import TokenType


def _split_save_id(tok):
    if tok.type_ != TokenType.DirectiveBodyItem:
        raise UnexpectedTokenError(tok.type_, TokenType.DirectiveBodyItem)
    save_to = tok.content.strip()
    if '.' in save_to:
        return tuple(save_to.split('.'))
    else:
        return (save_to,)


def _save_to(dest, name_parts, value):
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





class _SaveNode(namedtuple('_SaveNode', 'ident_parts')):
    __slots__ = ()
    def do(self, context):
        _save_to(context.rv, self.ident_parts, context.value)


def make_save(parser):
    tok = parser._next_tok()
    save_id_parts = _split_save_id(tok)
    return None, _SaveNode(save_id_parts)


class _SaveEachNode(namedtuple('_SaveEachNode', 'ident_parts sub_ctx_node')):
    __slots__ = ()
    def do(self, context):
        results = []
        _save_to(context.rv, self.ident_parts, results)
        for item in context.value:
            rv = {}
            results.append(rv)
            self.sub_ctx_node.do(None, rv, item, item)


def make_save_each(parser):
    tok = parser._next_tok()
    save_id_parts = _split_save_id(tok)
    # consume the context token and parse the sub-context SaveEachNode will manage
    tok = parser._next_tok()
    if tok.type_ != TokenType.Context:
        raise UnexpectedTokenError(tok.type_, TokenType.Context, token=tok)
    if tok.end <= parser._depth:
        raise TakeSyntaxError('Invalid depth, expecting to start a "save each" context.',
                              extra=tok)
    sub_ctx = parser.spawn_context_parser()
    sub_ctx_node, tok = sub_ctx.parse()
    sub_ctx.destroy()
    return tok, _SaveEachNode(save_id_parts, sub_ctx_node)


class _NamespaceNode(namedtuple('_NamespaceNode', 'ident_parts sub_ctx_node')):
    __slots__ = ()
    def do(self, context):
        sub_rv = {}
        _save_to(context.rv, self.ident_parts, sub_rv)
        self.sub_ctx_node.do(None, sub_rv, context.value, context.value)


def make_namespace(parser):
    tok = parser._next_tok()
    save_id_parts = _split_save_id(tok)
    # consume the context token and parse the sub-context SaveEachNode will manage
    tok = parser._next_tok()
    if tok.type_ != TokenType.Context:
        raise UnexpectedTokenError(tok.type_, TokenType.Context, token=tok)
    if tok.end <= parser._depth:
        raise TakeSyntaxError('Invalid depth, expecting to start a "namespace" context.',
                              extra=tok)
    sub_ctx = parser.spawn_context_parser()
    sub_ctx_node, tok = sub_ctx.parse()
    sub_ctx.destroy()
    return tok, _NamespaceNode(save_id_parts, sub_ctx_node)


DIRECTIVES = {
    'save':         make_save,
    ':':            make_save,
    'save each':    make_save_each,
    'namespace':    make_namespace,
    '+':            make_namespace,
}
