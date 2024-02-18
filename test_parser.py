import pytest

from my_lexer import Lexer
from my_parser import OldParser
from my_parser2 import NewParser
from my_ast import ASTCodeBlock, ASTDeclaration
from ast_print_visitor import PrintVisitor
from ast_codegen_visitor import CodegenVisitor


def parse(src_code, parser):
    lex = Lexer()
    tokens = lex.analyze(src_code)

    return parser.parse(tokens)


def create_parser(use_new):
    if use_new:
        return NewParser()
    return OldParser()


parser = create_parser(use_new=True)


def test_empty_src():
    code = '''{}'''
    ast = parse(code, parser)
    assert isinstance(ast, ASTCodeBlock) and len(ast.children) == 0
    ast.emit()


def test_declaration_int():
    code = ''' { var int x; }'''
    ast = parse(code, parser)
    assert isinstance(ast.children[0], ASTDeclaration)
    assert ast.children[0].tp.name == 'int' and ast.children[0].name.name == 'x'
    ast.emit()
    codegen = CodegenVisitor()
    ast.accept(codegen)
    print(codegen.bytecode)


def test_expression():
    code = '''{ 1 + 2 * (4+5); }'''
    ast = parse(code, parser)
    ast.emit()
    codegen = CodegenVisitor()
    ast.accept(codegen)
    print(codegen.bytecode)


def test_declaration_with_init():
    code = '''{ var int x = 1 + 2; }'''
    ast = parse(code, parser)
    ast.emit()
    codegen = CodegenVisitor()
    ast.accept(codegen)
    print(codegen.bytecode)


def test_use_variable():
    code = '''{ var int x = 1; var int y = x + 2; }'''
    ast = parse(code, parser)
    codegen = CodegenVisitor()
    ast.accept(codegen)
    print(codegen.bytecode)


def test_if():
    code = '''{ var int x = 1; if (x < 10) { x = 100; } x = 5; }'''
    ast = parse(code, parser)
    codegen = CodegenVisitor()
    ast.accept(codegen)
    print(codegen.bytecode)


def test_while():
    code = '''{ var int x = 1; while (x < 10) { x = x + 1; } }'''
    ast = parse(code, parser)
    codegen = CodegenVisitor()
    ast.accept(codegen)
    print(codegen.bytecode)


def test_function_declaration():
    code = '''
    {
        func int foo()
        {
            return 1;
        }
    }'''
    ast = parse(code, parser)
    # ast.accept(PrintVisitor())
    ast.emit()


def test_function_call():
    code = '''
    {
        func int foo(int x)
        {
            return x * 10;
        }
        
        foo(2);
    }'''
    ast = parse(code, parser)
    ast.accept(PrintVisitor())


def test_conditional():
    code = '''
    {
        var int x = 10;
        if (x < 100)
        {
            x = 0;
        }
    }'''
    ast = parse(code, parser)
    ast.accept(PrintVisitor())


def test_loop():
    code = '''
    {
        var int x = 10;
        while (x < 100)
        {
            x = x * 2;
        }
    }'''
    ast = parse(code, parser)
    ast.accept(PrintVisitor())


def test_function_call_two_args():
    code = '''
    {
        func int multiply(int x, int y)
        {
            return x * y;
        }
        
        multiply(2);
    }
    '''
    ast = parse(code, parser)
    ast.accept(PrintVisitor())
    ast.emit()
