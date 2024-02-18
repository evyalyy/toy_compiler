
class CompileError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class UndeclaredTypeError(CompileError):
    def __init__(self, type_name):
        super().__init__(f'Undeclared type: {type_name}')


class RedefinitionError(CompileError):
    def __init__(self, var_name):
        super().__init__(f'Variable {var_name} has already been declared')


class InvalidReturnError(CompileError):
    def __init__(self):
        super().__init__('Return statement outside function definition')


class UnexpectedTokenError(CompileError):

    def __init__(self, tok, pos):
        super().__init__(f'Unexpected token <{tok}> at position {pos}')
        self.tok = tok
        self.pos = pos


class LoopError(CompileError):

    def __init__(self, name, pos):
        super().__init__(f'<{name}> statement at pos {pos} is outside a loop')
        self.pos = pos
        self.name = name
