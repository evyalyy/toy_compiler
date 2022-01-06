from parser import Parser

from lexer import Lexer


if __name__ == '__main__':
    
    code = '''
        10 + 10
    '''

    lex = Lexer() 
    tokens = lex.analyze(code)