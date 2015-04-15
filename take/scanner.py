from collections import namedtuple
from enum import Enum
import re

from .exceptions import ScanError


_COMMENT_TEST_RX = re.compile(r'^\s*#.*$')
_CTX_WS_RX = re.compile(r'\S')
_INT_RX = re.compile(r'-?\d+')
_WS_RX = re.compile(r'\s+')


class Keywords(object):
    css_start = '$'
    accessor_start = '|'
    attr_accessor_start = '['
    attr_accessor_end = ']'
    text_accessor = 'text'
    own_text_accessor = 'own_text'
    field_accessor_start = '.'
    statement_end = ';'
    params_start = ':'
    continuation = ','


class KeywordSets(object):
    query_start = Keywords.css_start + Keywords.accessor_start
    css_query_end = Keywords.accessor_start + Keywords.statement_end
    directive_id_end = Keywords.params_start + Keywords.statement_end
    param_end = ' ' + Keywords.statement_end + Keywords.continuation


TokenType = Enum('TokenType', ' '.join((
    'Context',
    'QueryStatement',
    'QueryStatementEnd',
    'CSSSelector',
    'AccessorSequence',
    'IndexAccessor',
    'TextAccessor',
    'OwnTextAccessor',
    'AttrAccessor',
    'FieldAccessor',
    'DirectiveStatement',
    'DirectiveStatementEnd',
    'DirectiveIdentifier',
    'DirectiveBodyItem',
    'InlineSubContext'
    )))


class Token(namedtuple('Token', 'type_ content line line_num start end')):
    __slots__ = ()

    def __repr__(self):
        return ('Token: {{\n'
                '        type_: {!r}\n'
                '      content: "{}"\n'
                '     line num: {}\n'
                '   start, end: {}, {}\n'
                '         line: "{}"\n'
                '}}').format(self.type_, self.content, self.line_num, self.start, self.end, self.line)


class Scanner(object):

    def __init__(self, fobj):
        self.fobj = fobj
        self.line_gen = None
        self.line = None
        self.line_num = 0
        self.start = 0
        self.pos = 0

    @property
    def _c(self):
        return self.line[self.pos]

    @property
    def _eol(self):
        return self.pos >= len(self.line)

    @property
    def _to_eol_content(self):
        return self.line[self.start:]

    @property
    def _tok_content(self):
        return self.line[self.start:self.pos]

    def scan(self):
        while bool(self._next_line()):
            if _COMMENT_TEST_RX.match(self.line):
                continue
            scan_fn = self._scan_context
            while scan_fn:
                scan_fn, tok = scan_fn()
                if tok:
                    yield tok

    def _next_line(self):
        if not self.line_gen:
            self.line_gen = iter(self.fobj)
        while True:
            try:
                self.line = next(self.line_gen).rstrip()
            except StopIteration:
                self.line_gen = None
                self.line = None
                self.start = self.pos -1
                return None
            self.start = self.pos = 0
            self.line_num += 1
            if self.line:
                return self.line

    def _ignore(self):
        self.start = self.pos

    def _make_token(self, type_):
        tok = Token(type_,
                    self.line[self.start:self.pos],
                    self.line,
                    self.line_num,
                    self.start,
                    self.pos)
        self.start = self.pos
        return tok

    def _make_marker_token(self, type_):
        """Make a token that has no content"""
        tok = Token(type_,
                    '',
                    self.line,
                    self.line_num,
                    self.start,
                    self.start)
        return tok

    def _accept(self, valid=None, alpha=False, num=False, alphanum=False):
        if self._eol:
            return False
        ok = False
        if valid and self._c in valid:
            ok = True
        elif alpha and self._c.isalpha():
            ok = True
        elif num and self._c.isdigit():
            ok = True
        elif alphanum and self._c.isalnum():
            ok = True
        elif not valid and not alpha and not num and not alphanum:
            raise ScanError.make(self, 'Invalid _accept call, valid or preset not specified')
        if ok:
            self.pos += 1
        return ok

    def _accept_run(self, valid=None, alpha=False, num=False, alphanum=False):
        count = 0
        tests = []
        if valid:
            tests.append(lambda: self._c in valid)
        if alpha:
            tests.append(lambda: self._c.isalpha())
        if num:
            tests.append(lambda: self._c.isdigit())
        if alphanum:
            tests.append(lambda: self._c.isalnum())
        if not tests:
            raise ScanError.make(self, 'Invalid _accept call, valid or preset not specified')
        while not self._eol and any(t() for t in tests):
            count += 1
            self.pos += 1
        return count

    def _accept_until(self, one_of):
        count = 0
        while not self._eol and self._c not in one_of:
            count += 1
            self.pos += 1
        return count

    def _consume(self, val):
        if self._eol:
            return False
        next_pos = self.pos + len(val)
        if self.line[self.pos:next_pos] == val:
            self.pos = next_pos
            return True
        return False

    def _consume_re(self, test_re):
        if self._eol:
            return False
        m = test_re.match(self._to_eol_content)
        if not m:
            return False
        self.pos += m.end()
        return True


    def _scan_context(self):
        m = _CTX_WS_RX.search(self.line)
        if not m:
            raise ScanError.make(self, 'Invalid state: error parsing context')
        self.pos = m.start()
        tok = self._make_token(TokenType.Context)
        return self._scan_statement, tok

    def _scan_statement(self):
        if self._c in KeywordSets.query_start:
            tok = self._make_marker_token(TokenType.QueryStatement)
            return self._scan_query, tok
        else:
            tok = self._make_marker_token(TokenType.DirectiveStatement)
            return self._scan_directive, tok

    def _scan_directive(self):
        # a directive without any text is valid, considered an alias to "save",
        # use ":" as the directive ID
        if self._accept(Keywords.params_start):
            tok = self._make_token(TokenType.DirectiveIdentifier)
            return self._scan_directive_body, tok
        elif self._accept_until(KeywordSets.directive_id_end) < 1:
            raise ScanError.make(self, 'Invalid directive, 0 length')
        tok = self._make_token(TokenType.DirectiveIdentifier)
        if self._eol or self._c == Keywords.statement_end:
            return self._end_directive, tok
        elif self._accept(Keywords.params_start):
            self._ignore()
            return self._scan_directive_body, tok
        else:
            raise ScanError.make(self, 'Invalid directive identifier terminator: '
                                       '%r. Either %r, %r or end of the line required.' %
                                       (self._to_eol_content,
                                        Keywords.params_start,
                                        Keywords.statement_end))

    def _scan_directive_body(self):
        self._accept_run(' ')
        self._ignore()
        if self._eol or self._c == Keywords.statement_end:
            return self._end_directive()

        if self._c == Keywords.continuation:
            self._accept(Keywords.continuation)
            self._accept_run(' ')
            self._ignore()
            if self._eol and not self._next_line():
                raise ScanError.make(self, 'Unexpected EOF, directive parameter expected.')
            self._consume_re(_WS_RX)
        if self._accept_until(KeywordSets.param_end) < 1:
            raise ScanError.make(self, 'Invalid directive body item, 0 length')
        tok = self._make_token(TokenType.DirectiveBodyItem)
        return self._scan_directive_body, tok

    def _end_directive(self):
        tok = self._make_marker_token(TokenType.DirectiveStatementEnd)
        if self._eol:
            return None, tok
        elif self._c == Keywords.statement_end:
            return self._scan_inline_sub_ctx, tok
        else:
            raise ScanError.make(self, 'Invalid end of directive statement: %r' % self._to_eol_content)

    def _scan_query(self):
        if self._c == Keywords.css_start:
            return self._scan_css_selector()
        elif self._c == Keywords.accessor_start:
            return self._scan_accessor_sequence()
        else:
            raise ScanError.make(self, 'Invalid query statement: %r' % self._to_eol_content)

    def _end_query(self):
        tok = self._make_marker_token(TokenType.QueryStatementEnd)
        if self._eol:
            return None, tok
        elif self._c == Keywords.statement_end:
            return self._scan_inline_sub_ctx, tok
        else:
            raise ScanError.make(self, 'Invalid end of query statement: %r' % self._to_eol_content)

    def _scan_css_selector(self):
        self._accept(Keywords.css_start)
        self._accept_run(' ')
        self._ignore()
        if self._accept_until(KeywordSets.css_query_end) < 1:
            raise ScanError.make(self, 'Invalid CSS Selector: %r' % self._to_eol_content)
        tok = self._make_token(TokenType.CSSSelector)
        if self._eol or self._c == Keywords.statement_end:
            return self._end_query, tok
        elif self._c == Keywords.accessor_start:
            return self._scan_accessor_sequence, tok
        else:
            raise ScanError.make(self, 'EOL or accessor sequence expected, instead found %r' % self._to_eol_content)

    def _scan_accessor_sequence(self):
        # create the marker token at the start of the sequence
        tok = self._make_marker_token(TokenType.AccessorSequence)
        # skip the initial marker character
        self._accept(Keywords.accessor_start)
        self._ignore()
        return self._scan_accessor, tok

    def _scan_accessor(self):
        self._accept_run(' ')
        self._ignore()
        if self._eol or self._c == Keywords.statement_end:
            return self._end_query()
        # attribute accessor
        elif self._c == Keywords.attr_accessor_start:
            self._accept_until(Keywords.attr_accessor_end)
            if not self._accept(Keywords.attr_accessor_end):
                raise ScanError.make(self, 'Invalid Attr Accessor: %r' % self._to_eol_content)
            tok = self._make_token(TokenType.AttrAccessor)
            return self._scan_accessor, tok
        # text accessor
        elif self._consume(Keywords.text_accessor):
            tok = self._make_token(TokenType.TextAccessor)
            return self._scan_accessor, tok
        # own text accessor
        elif self._consume(Keywords.own_text_accessor):
            tok = self._make_token(TokenType.OwnTextAccessor)
            return self._scan_accessor, tok
        # field accessor, ex: `| .field_name`
        elif self._consume(Keywords.field_accessor_start):
            if self._accept_until(' ') < 1:
                raise ScanError.make(self, 'Invalid field accessor, exepected field '
                                           'name instead found: %r' % self._to_eol_content)
            tok = self._make_token(TokenType.FieldAccessor)
            return self._scan_accessor, tok
        else:
            # index accesor, test for a valid number, ie -?\d+
            if not self._consume_re(_INT_RX):
                raise ScanError.make(self, 'Expected an accessor, instead found: %r' % self._to_eol_content)
            tok = self._make_token(TokenType.IndexAccessor)
            return self._scan_accessor, tok

    def _scan_inline_sub_ctx(self):
        self._accept_run(Keywords.statement_end)
        tok = self._make_token(TokenType.InlineSubContext)
        self._accept_run(' ')
        self._ignore()
        return self._scan_statement, tok
