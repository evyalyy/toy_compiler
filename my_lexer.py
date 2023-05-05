from preprocessing import remove_comments
from enum import Enum


class TokenType(Enum):
    NUM, ID, \
        IF, ELSE, WHILE, DO, \
        LEFT_BRACKET, RIGHT_BRACKET, LEFT_PARENTHESIS, RIGHT_PARENTHESIS, \
        PLUS, MINUS, MUL, DIV, \
        LESS, EQUAL, NOT_EQUAL, GE, LE, \
        SEMICOLON, EOF, WHITESPACE = range(22)


class Token:

    def __init__(self, lexeme=None, tp=None, value=None):
        self.lexeme = lexeme
        self.type = tp
        self.value = value

        self.line_no = None
        self.line_pos = None

    def set_location(self, line_no, line_pos):
        self.line_no = line_no
        self.line_pos = line_pos - len(self.lexeme)

    def __str__(self):
        v = str(self.value) if self.value is not None else 'None'
        return f'Token(\"{self.lexeme}\",{self.type},{v}, at {self.line_no}:{self.line_pos})'


class LexerState(Enum):
    START_TOKEN = 0
    CONTINUE_TOKEN = 1


class Lexer:
    keywords = ['if', 'else', 'while', 'break', 'continue', 'var', 'func', 'entry', 'return']

    op_map = {'+': 'plus', '-': 'minus', '=': 'assign', '*': 'multiply', '/': 'divide', '<': 'less', '>': 'greater',
              '==': 'equal', '!=': 'notequal'}

    def __init__(self, comment_mark='//'):

        self.comment_mark = comment_mark
        self.lex_begin = 0
        self.curr_pos = 0
        self.code = ''

        self.state = LexerState.START_TOKEN

        self.curr_line_no = 0
        self.curr_pos_in_line = 0

        setattr(self, 'test_semicolon', lambda: self._test_one_sym(';'))
        setattr(self, 'test_colon', lambda: self._test_one_sym(','))

        setattr(self, 'test_lcurv', lambda: self._test_one_sym('{'))
        setattr(self, 'test_rcurv', lambda: self._test_one_sym('}'))

        setattr(self, 'test_lsquare', lambda: self._test_one_sym('['))
        setattr(self, 'test_rsquare', lambda: self._test_one_sym(']'))

        setattr(self, 'test_lparen', lambda: self._test_one_sym('('))
        setattr(self, 'test_rparen', lambda: self._test_one_sym(')'))

        setattr(self, 'test_star', lambda: self._test_one_sym('*'))

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

    def _test_one_sym(self, sym):
        c = self.code[self.curr_pos]
        if c == sym:
            self.adv()
            return True
        else:
            return False

    def test_id(self):

        self.state = LexerState.START_TOKEN
        code_len = len(self.code)
        while self.curr_pos < code_len:
            c = self.code[self.curr_pos]

            if self.state == LexerState.START_TOKEN:
                if c.isalpha() or c == '_':
                    self.move_adv(LexerState.CONTINUE_TOKEN)
                    continue

                return False
            if self.state == LexerState.CONTINUE_TOKEN:
                if c.isalpha() or c.isdigit() or c == '_':
                    self.adv()
                    continue

                return True

    def test_number(self):

        self.state = LexerState.START_TOKEN
        code_len = len(self.code)
        while self.curr_pos < code_len:
            c = self.code[self.curr_pos]
            if self.state == LexerState.START_TOKEN:
                if c.isdigit():
                    self.move_adv(LexerState.CONTINUE_TOKEN)
                    continue

                return False
            if self.state == LexerState.CONTINUE_TOKEN:
                if c.isdigit():
                    self.adv()
                    continue
                return True

    def test_whitespace(self):

        self.state = LexerState.START_TOKEN
        code_len = len(self.code)
        while self.curr_pos < code_len:
            c = self.code[self.curr_pos]
            if self.state == LexerState.START_TOKEN:
                if c in [' ', '\n', '\t']:
                    self.move_adv(LexerState.CONTINUE_TOKEN)
                    continue
                return False
            if self.state == LexerState.CONTINUE_TOKEN:
                if c in [' ', '\n', '\t']:
                    self.adv()
                    continue

                return True

    def test_operator(self):
        self.state = LexerState.START_TOKEN
        code_len = len(self.code)
        while self.curr_pos < code_len:
            c = self.code[self.curr_pos]
            if self.state == LexerState.START_TOKEN:
                if c in ['=', '+', '-', '<', '>', '*', '!']:
                    self.move_adv(LexerState.CONTINUE_TOKEN)
                    continue
                return False
            if self.state == LexerState.CONTINUE_TOKEN:
                if c in ['=']:
                    self.adv()
                    continue
                return True

    def get_lexeme(self):
        return self.code[self.lex_begin:self.curr_pos]

    def analyze(self, code):

        self.code = remove_comments(code, self.comment_mark)
        self.lex_begin = 0
        self.curr_pos = 0

        self.curr_line_no = 0

        tests = [s for s in dir(self) if s.startswith('test_')]
        tokens = []
        while self.curr_pos < len(self.code):

            # print('On pos:',self.curr_pos)
            # print('Context:',code[self.curr_pos-10:self.curr_pos+10])

            for i, t in enumerate(tests):

                # print('Testing',t)
                ret = getattr(self, t)()
                if not ret:
                    continue

                token_name = t.replace('test_', '')
                lexeme = self.get_lexeme()

                self.lex_begin = self.curr_pos

                if token_name == 'whitespace':
                    continue

                token = Token(lexeme, token_name)
                token.set_location(self.curr_line_no, self.curr_pos_in_line)
                if token_name == 'number':
                    token.value = int(lexeme)
                if token_name == 'id':
                    if lexeme in Lexer.keywords:
                        token.type = lexeme

                if token_name == 'operator':
                    token.type = Lexer.op_map[lexeme]

                tokens.append(token)

        return tokens


if __name__ == '__main__':

    source_code = '''
10 + 10
// foo + bar
int x = 10;// this is a comment
'''

    lex = Lexer()
    parsed_tokens = lex.analyze(source_code)

    for tok in parsed_tokens:
        print(tok)
