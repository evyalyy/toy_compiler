import pytest

from my_lexer import Lexer
from my_parser import OldParser
from my_parser2 import NewParser


def parse(src_code, parser):
    lex = Lexer()
    tokens = lex.analyze(src_code)

    ast = parser.parse(tokens)

    return ast.emit()


def create_parser(use_new):
    if use_new:
        return NewParser()
    return OldParser()


parser = create_parser(True)


def test_empty_src():
    code = '''{}'''
    bytecode = parse(code, parser)
    assert bytecode == []
