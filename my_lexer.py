from preprocessing import remove_comments
from enum import Enum
import re
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

    def __init__(self, lexeme=None, tp=None, value=None):
        self.lexeme = lexeme
        self.type = tp
        self.value = value

        self.location = None

    def set_location(self, line_no, line_pos):
        self.location = TokenLocation(line_no, line_pos - len(self.lexeme))

    def __str__(self):
        v = str(self.value) if self.value is not None else 'None'
        return f'Token(\"{self.lexeme}\",{self.type},{v}, at {self.location})'


class LexerState(Enum):
    START_TOKEN = 0
    CONTINUE_TOKEN = 1


class Lexer:
    keywords = {
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'break': TokenType.BREAK,
        'continue': TokenType.CONTINUE,
        'var': TokenType.VAR,
        'func': TokenType.FUNC,
        'entry': TokenType.ENTRY,
        'return': TokenType.RETURN
    }

    punctuation = {
        r'\{': TokenType.LEFT_CURL,
        r'\}': TokenType.RIGHT_CURL,
        r'\[': TokenType.LEFT_BRACKET,
        r'\]': TokenType.RIGHT_BRACKET,
        r'\(': TokenType.LEFT_PARENTHESIS,
        r'\)': TokenType.RIGHT_PARENTHESIS,
        r';': TokenType.SEMICOLON,
        r'\,': TokenType.COMMA
    }

    operators = {
        r'\+': TokenType.PLUS,
        r'\-': TokenType.MINUS,
        r'\*': TokenType.MUL,
        '/': TokenType.DIV,
        '=': TokenType.ASSIGN,
        r'\>': TokenType.GE,
        r'\<': TokenType.LE
    }

    operators_two_symbols = {
        '==': TokenType.EQUAL,
        '!=': TokenType.NOT_EQUAL
    }

    def __init__(self, comment_mark='//'):

        self.comment_mark = comment_mark
        self.lex_begin = 0
        self.curr_pos = 0
        self.code = ''

        self.state = LexerState.START_TOKEN

        self.curr_line_no = 0
        self.curr_pos_in_line = 0

        self.generic_tests = []
        self.add_regex_test(TokenType.ID, r'[a-zA-Z_]\w*')
        self.add_regex_test(TokenType.NUM, r'\d+')
        self.add_regex_test(TokenType.WHITESPACE, r'\s+', False)
        for pat, token_type in self.punctuation.items():
            self.add_regex_test(token_type, pat)
        # NOTE: two-symbol operators like `==` or `!=` must be added before `=` test
        for pat, token_type in self.operators_two_symbols.items():
            self.add_regex_test(token_type, pat)
        for pat, token_type in self.operators.items():
            self.add_regex_test(token_type, pat)

    def move_adv(self, st):
        self.state = st
        self.adv()

    def adv(self):
        if self.code[self.curr_pos] == '\n':
            self.curr_line_no += 1
            self.curr_pos_in_line = 0
        else:
            self.curr_pos_in_line += 1

        self.curr_pos += 1

    def regex_test(self, pattern: re.Pattern, use_eol=True):
        eol = len(self.code)
        if use_eol:
            next_newline = self.code.find('\n', self.curr_pos)
            if next_newline != -1:
                eol = next_newline
        m = pattern.match(self.code, self.curr_pos, eol)
        if m:
            for i in range(m.end()-m.start()):
                self.adv()
            return True
        return False

    def add_regex_test(self, token_type: TokenType, pattern: str, use_eol=True):
        self.generic_tests.append((token_type, re.compile(pattern, re.ASCII), use_eol))

    def get_lexeme(self):
        return self.code[self.lex_begin:self.curr_pos]

    def analyze(self, code):

        self.code = remove_comments(code, self.comment_mark)
        self.lex_begin = 0
        self.curr_pos = 0

        self.curr_line_no = 0

        tokens = []
        while self.curr_pos < len(self.code):

            for token_type, pattern, use_eol in self.generic_tests:

                found = self.regex_test(pattern, use_eol)
                if not found:
                    continue

                lexeme = self.get_lexeme()

                self.lex_begin = self.curr_pos

                if token_type == TokenType.WHITESPACE:
                    continue

                token = Token(lexeme, token_type)
                token.set_location(self.curr_line_no, self.curr_pos_in_line)

                if token_type == TokenType.NUM:
                    token.value = int(lexeme)
                if token_type == TokenType.ID:
                    if lexeme in Lexer.keywords:
                        token.type = Lexer.keywords.get(lexeme)

                tokens.append(token)

        return tokens


if __name__ == '__main__':

    source_code = '''
10 + 10
foo + bar
int x = 10;// this is a comment
int xy1_zd = abcd
while (x < 1) { var tmp y = 1; y == 100; }
'''

    lex = Lexer()
    parsed_tokens = lex.analyze(source_code)

    for tok in parsed_tokens:
        print(tok)
