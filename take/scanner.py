from collections import namedtuple
from enum import Enum
import re


_COMMENT_TEST_RX = re.compile(r'^\s*#.*$')
_CTX_WS_RX = re.compile(r'\S')
_INT_RX = re.compile(r'-?\d+')


class Keywords(object):
    css_start_delim = '$'
    accessor_start_delim = '|'
    attr_accessor_start = '['
    attr_accessor_end = ']'
    text_accessor = 'text'


TokenType = Enum('TokenType', ' '.join((
    'Context',
    'QueryStatement',
    'QueryStatementEnd',
    'CSSSelector',
    'AccessorSequence',
    'IndexAccessor',
    'TextAccessor',
    'AttrAccessor',
    'DirectiveStatement',
    'DirectiveIdentifier',
    'DirectiveBodyItem',
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


class ScanError(Exception):

    @staticmethod
    def make(scanner, msg, extra=None):
        return ScanError(msg, scanner.line, scanner.line_num, scanner.pos, extra)

    def __init__(self, message, line, line_num, pos, extra=None):
        self.message = message
        self.line = line
        self.line_num = line_num
        self.pos = pos
        self.extra = extra

    def __str__(self):
        return ('ScanError: {{\n'
                '      message: {!r}\n'
                '         line: "{}"\n'
                '                {}^\n'
                '     line num: {}\n'
                '          pos: {}\n'
                '        extra: {!r}\n'
                '}}').format(self.message, self.line, ' ' * self.pos,
                                              self.line_num, self.pos, self.extra)


class Scanner(object):

    def __init__(self, fobj):
        self.fobj = fobj
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
        for line in self.fobj:
            self.line_num += 1
            self.start = self.pos = 0
            self.line = line.rstrip()
            if not self.line or _COMMENT_TEST_RX.match(self.line):
                continue
            scan_fn = self._scan_context
            while scan_fn:
                scan_fn, tok = scan_fn()
                if tok:
                    yield tok

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
        if self._c.isalpha():
            tok = self._make_marker_token(TokenType.DirectiveStatement)
            return self._scan_directive, tok
        else:
            tok = self._make_marker_token(TokenType.QueryStatement)
            return self._scan_query_statement, tok

    def _scan_directive(self):
        ok = self._accept(alpha=True)
        if not ok:
            raise ScanError.make(self, 'Invalid directive, must start with an alpha, not %s' % self._c)
        if self._accept_until(':') < 1:
            raise ScanError.make(self, 'Invalid directive, 0 length')
        tok = self._make_token(TokenType.DirectiveIdentifier)
        if not self._accept(':'):
            raise ScanError.make(self, 'Invalid directive identifier terminator: "%s", ":" required.' % self._tok_content)
        self._ignore()
        return self._scan_directive_body, tok

    def _scan_directive_body(self):
        self._accept_run(' ')
        self._ignore()
        if self._accept_until(' ') < 1:
            raise ScanError.make(self, 'Invalid directive body item, 0 length')
        tok = self._make_token(TokenType.DirectiveBodyItem)
        return None if self._eol else self._scan_directive_body, tok

    def _scan_query_statement(self):
        if self._c == Keywords.css_start_delim:
            return self._scan_css_selector()
        elif self._c == Keywords.accessor_start_delim:
            return self._scan_accessor_sequence()
        else:
            raise ScanError.make(self, 'Invalid query statement: %s' % self._to_eol_content)

    def _end_query_statement(self):
        tok = self._make_marker_token(TokenType.QueryStatementEnd)
        return None, tok

    def _scan_css_selector(self):
        self._accept(Keywords.css_start_delim)
        self._accept_run(' ')
        self._ignore()
        if self._accept_until(Keywords.accessor_start_delim) < 1:
            raise ScanError.make(self, 'Invalid CSS Selector: %s' % self._to_eol_content)
        tok = self._make_token(TokenType.CSSSelector)
        if self._eol:
            return self._end_query_statement, tok
        elif self._c == Keywords.accessor_start_delim:
            return self._scan_accessor_sequence, tok
        else:
            raise ScanError.make(self, 'EOL or accessor sequence expected, instead found %s' % self._to_eol_content)

    def _scan_accessor_sequence(self):
        # create the marker token at the start of the sequence
        tok = self._make_marker_token(TokenType.AccessorSequence)
        # skip the initial marker character
        self._accept(Keywords.accessor_start_delim)
        self._ignore()
        return self._scan_accessor, tok

    def _scan_accessor(self):
        self._accept_run(' ')
        self._ignore()
        if self._eol:
            return self._end_query_statement()
        elif self._c == Keywords.attr_accessor_start:
            # attribute accessor
            self._accept_until(Keywords.attr_accessor_end)
            if not self._accept(Keywords.attr_accessor_end):
                raise ScanError.make(self, 'Invalid Attr Accessor: %s' % self._to_eol_content)
            tok = self._make_token(TokenType.AttrAccessor)
            return self._scan_accessor, tok
        elif self._consume(Keywords.text_accessor):
            # text accessor
            tok = self._make_token(TokenType.TextAccessor)
            return self._scan_accessor, tok
        else:
            # index accesor, test for a valid number, ie -?\d+
            if not self._consume_re(_INT_RX):
                raise ScanError.make(self, 'Expected an accessor, instead found: %s' % self._to_eol_content)
            tok = self._make_token(TokenType.IndexAccessor)
            return self._scan_accessor, tok
