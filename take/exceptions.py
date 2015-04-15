
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


class AlreadyParsedError(Exception):
    pass


class UnexpectedEOFError(Exception):
    pass


class UnexpectedTokenError(Exception):
    def __init__(self, found, expected, message=None, token=None):
        self.found = found
        self.expected = expected
        self.message = message
        self.token = token

    def __str__(self):
        return ('UnexpectedTokenError {{\n'
                '       found: {!r}\n'
                '    expected: {!r}\n'
                '         message: {!r}\n'
                '       token: {}\n'
                '}}').format(self.found, self.expected, self.message, self.token)


class InvalidDirectiveError(Exception):
    def __init__(self, ident, message=None):
        self.ident = ident
        self.message = message

    def __str__(self):
        return ('InvalidDirectiveError {{\n'
                '      ident: {!r}\n'
                '    message: {!r}\n'
                '}}').format(self.ident, self.message)


class TakeSyntaxError(Exception):
    def __init__(self, message, extra=None):
        self.message = message
        self.extra = extra

    def __str__(self):
        return ('TakeSyntaxError {{\n'
                '      message: {!r}\n'
                '        extra: {!r}\n'
                '}}').format(self.message, self.extra)
