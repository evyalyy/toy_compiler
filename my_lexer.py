
class Token:

    # NUM, ID, IF, ELSE, WHILE, DO, LBRA, RBRA, LPAR, RPAR, PLUS, MINUS, LESS, \
    # EQUAL, SEMICOLON, EOF = range(16)

    def __init__(self, lexeme=None, tp=None, value=None):
        self.lexeme = lexeme
        self.type = tp
        self.value = value

        self.line_no = None
        self.line_pos = None

    def __str__(self):
        v = str(self.value) if self.value is not None else 'None'
        return '(\"%s\",%s,%s)' % (self.lexeme, self.type, v)


def preprocess(code, comment_sym='//'):
    curr_idx = 0
    n = len(code)
    lines = code.split('\n')
    # print(lines)
    out_lines = []
    # print('Preprocessing')
    for line in lines:
        comment_start = line.find(comment_sym)
        # print('line:','"%s"' % line)
        # print('Found comment:',comment_start)
        if comment_start < 0:
            out_lines.append(line)
            continue
        line = line[:comment_start]
        # print('After comment removal:','"%s"' % line)
        out_lines.append(line)

    # print(out_lines)
    return '\n'.join(out_lines)


class Lexer:
    keywords = ['if', 'else', 'while', 'break', 'continue', 'var', 'func', 'entry', 'return']

    op_map = {'+': 'plus', '-': 'minus', '=': 'assign', '*': 'multiply', '/': 'divide'}
    op_map['<'] = 'less'
    op_map['>'] = 'greater'
    op_map['=='] = 'equal'
    op_map['!='] = 'notequal'

    def __init__(self, symtable=None):

        # self.symtable = symtable
        self.lex_begin = 0
        self.curr_pos = 0
        self.code = ''

        self.state = 0

        self.curr_line_no = 0
        self.last_newline = None

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
        self.curr_pos += 1

    def adv(self):
        self.curr_pos += 1

    def _test_one_sym(self, sym):
        c = self.code[self.curr_pos]
        if c == sym:
            self.adv()
            return True
        else:
            return False

    def test_id(self):

        self.state = 0
        code_len = len(self.code)
        while self.curr_pos < code_len:
            c = self.code[self.curr_pos]

            if self.state == 0:
                if c.isalpha() or c == '_':
                    self.move_adv(1)
                    continue

                return False
            if self.state == 1:
                if c.isalpha() or c.isdigit() or c == '_':
                    self.adv()
                    continue

                return True

    def test_number(self):

        self.state = 0
        code_len = len(self.code)
        while self.curr_pos < code_len:
            c = self.code[self.curr_pos]
            if self.state == 0:
                if c.isdigit():
                    self.move_adv(1)
                    continue

                return False
            if self.state == 1:
                if c.isdigit():
                    self.adv()
                    continue
                return True

    def test_whitespace(self):

        self.state = 0
        code_len = len(self.code)
        while self.curr_pos < code_len:
            c = self.code[self.curr_pos]
            if self.state == 0:
                if c in [' ', '\n', '\t']:
                    self.move_adv(1)
                    continue
                return False
            if self.state == 1:
                if c in [' ', '\n', '\t']:
                    self.adv()
                    continue

                return True

    def test_operator(self):
        self.state = 0
        code_len = len(self.code)
        while self.curr_pos < code_len:
            c = self.code[self.curr_pos]
            if self.state == 0:
                if c in ['=', '+', '-', '<', '>', '*', '!']:
                    self.move_adv(1)
                    continue
                return False
            if self.state == 1:
                if c in ['=']:
                    self.adv()
                    continue
                return True

    def get_lexeme(self):
        return self.code[self.lex_begin:self.curr_pos]

    def analyze(self, code):

        self.code = preprocess(code, '#')
        self.code = preprocess(self.code, '//')
        self.lex_begin = 0
        self.curr_pos = 0

        self.curr_line_no = 0
        self.last_newline = None

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

                tname = t.replace('test_', '')
                lexeme = self.get_lexeme()

                self.lex_begin = self.curr_pos

                if tname == 'whitespace':
                    # print(tname,'"%s"' % lexeme)
                    # if '\n' in lexeme:
                    #     self.curr_line_no += 1
                    #     self.last_newline = self.curr_pos
                    #     s = '"%s"' % self.code[self.curr_pos-5:self.curr_pos+5]
                    #     print(self.curr_line_no,self.last_newline,s)
                    continue

                tok = Token(lexeme, tname)
                if tname == 'number':
                    tok.value = int(lexeme)
                if tname == 'id':
                    if lexeme in Lexer.keywords:
                        tok.type = lexeme

                if tname == 'operator':
                    tok.type = Lexer.op_map[lexeme]

                # tok = (lexeme,tname)

                tokens.append(tok)

        return tokens


if __name__ == '__main__':

    code = '''
10 + 10
// foo + bar
int x = 10;// this is a comment
'''

    lex = Lexer()
    tokens = lex.analyze(code)

    for t in tokens:
        print(t)
