
class CompileError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class InvalidReturnError(CompileError):
    def __init__(self):
        pass

    def __str__(self):
        return 'Return statement outside function definition'


class UnexpectedTokenError(CompileError):

    def __init__(self, tok, pos):
        self.tok = tok
        self.pos = pos

    def __str__(self):
        return f'Unexpected token <{self.tok}> at position {self.pos}'


class LoopError(CompileError):

    def __init__(self, name, pos):
        self.pos = pos
        self.name = name

    def __str__(self):
        return f'<{self.name}> statement at pos {self.pos} is outside a loop'
