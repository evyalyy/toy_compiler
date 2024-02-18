from enum import Enum
from dataclasses import dataclass


class TokenType(Enum):
    NUM, ID, \
        IF, ELSE, WHILE, CONTINUE, BREAK, VAR, FUNC, ENTRY, RETURN, \
        LEFT_CURL, RIGHT_CURL, LEFT_BRACKET, RIGHT_BRACKET, LEFT_PARENTHESIS, RIGHT_PARENTHESIS, \
        PLUS, MINUS, MUL, DIV, ASSIGN, \
        LESS, EQUAL, NOT_EQUAL, GE, LE, \
        SEMICOLON, COMMA, EOF, WHITESPACE = range(31)


@dataclass
class TokenLocation:
    line_no: int
    line_pos: int

    def __str__(self):
        return f'line:{self.line_no},pos:{self.line_pos}'


class Token:

    def __init__(self, lexeme, tp, line_no, line_pos, value=None):
        self.lexeme = lexeme
        self.type = tp
        self.value = value

        self.location = TokenLocation(line_no, line_pos - len(self.lexeme))

    def __str__(self):
        v = str(self.value)
        return f'Token(\"{self.lexeme}\",{self.type},{v}, at {self.location})'
