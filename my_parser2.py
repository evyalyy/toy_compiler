from parser import Parser

from my_token import TokenType, Token

from my_ast import ASTDeclaration, ASTExpr, ASTId, ASTNumber, ASTCodeBlock, ASTFunctionDefinition, ASTIfStatement, \
    ASTWhileStatement, ASTBreakStatement, ASTContinueStatement, ASTReturnStatement, ASTFunctionCall, ASTEntryPoint

from errors import UnexpectedTokenError
from ast_print_visitor import PrintVisitor

'''

expr -> assignment_expr

assignment_expr = additive_expr
                | postfix_expression = assignment_expr

assignment_expr = additive_expr assignment_expr_rest
assignment_expr_rest = '=' assignment_expr_rest

additive_expr  -> term additive_expr_rest        
additive_expr_rest  -> + term additive_expr_rest
                     | - term additive_expr_rest
                     | e
term      ->   postfix_expression term_rhs
term_rhs  -> * postfix_expression term_rhs
           | / postfix_expression term_rhs
           | e

postfix_expression -> primary_expression postfix_expression_rest
postfix_expression_rest -> [ expr ] postfix_expression_rest
                         | ( expr ) postfix_expression_rest
                         | ++ postfix_expression_rest
                         | -- postfix_expression_rest
                         | e

primary_expression -> number | ( expr )
'''


class NewParser(Parser):

    def __init__(self, ):
        self.curr_sym = None
        self.idx = -1

        self.tokens = []

        self.root = None

    def _reset(self):
        self.curr_sym = None
        self.idx = -1

        self.root = None

    def parse(self, tokens):
        self.tokens = tokens
        self._reset()
        self.advance()
        return self.program()

    def error_(self):
        raise UnexpectedTokenError(self.sym(), self.idx)

    def eof(self):
        return self.idx == len(self.tokens)

    def sym(self) -> Token:
        return self.curr_sym

    def expect(self, tp: TokenType, match=False):
        s = self.sym()
        if tp != s.type:
            return False

        if match:
            self.match(tp)
        return True

    def expect_many(self, tps):

        for s in tps:
            if self.expect(s):
                return True
        return False

    def match(self, tp: TokenType):
        s = self.sym()
        if tp != s.type:
            self.error_()

        self.advance()

    def advance(self):
        self.idx += 1
        if self.eof():
            print('finish parsing')
            return False
        self.curr_sym = self.tokens[self.idx]
        print(f'Advanced to symbol {self.curr_sym}')
        return True

    def program(self):

        node = self.code_block()

        if not self.eof():
            self.error_()

        return node

    def code_block(self):

        self.match(TokenType.LEFT_CURL)

        stmt_nodes = self.statement_list()

        curr_node = ASTCodeBlock()
        for stmt in stmt_nodes:
            curr_node.add_child(stmt)

        self.match(TokenType.RIGHT_CURL)

        return curr_node

    def statement_list(self):

        # FIRST(statement)
        possible_tokens = [TokenType.LEFT_PARENTHESIS,
                           TokenType.VAR, TokenType.FUNC, TokenType.RETURN, TokenType.IF, TokenType.LEFT_CURL,
                           TokenType.ID, TokenType.WHILE, TokenType.CONTINUE, TokenType.BREAK,
                           TokenType.NUM, TokenType.ENTRY]

        print('Current token:', self.sym())
        nodes = []
        if self.expect_many(possible_tokens):
            curr_node = self.statement()

            nodes.append(curr_node)
            nodes += self.statement_list()

        # Do nothing for epsilon production
        return nodes

    def statement(self):

        if self.expect(TokenType.VAR):
            dec = self.variable_declaration()
            self.match(TokenType.SEMICOLON)
            return dec

        if self.expect(TokenType.FUNC):
            func_def = self.function_definition()
            return func_def

        if self.expect(TokenType.RETURN, True):
            return self.return_statement()

        # expecting symbol from FIRST(expression)
        if self.expect_many([TokenType.ID, TokenType.LEFT_PARENTHESIS, TokenType.NUM]):
            expr = self.expression()
            self.match(TokenType.SEMICOLON)
            return expr

        if self.expect(TokenType.IF):
            print('IF statement')
            return self.if_statement()

        if self.expect(TokenType.WHILE):
            print('WHILE statement')
            return self.while_statement()

        if self.expect(TokenType.CONTINUE):
            print('Continue')
            cont = self.continue_statement()
            self.match(TokenType.SEMICOLON)
            return cont

        if self.expect(TokenType.BREAK):
            print('Break')
            br = self.break_statement()
            self.match(TokenType.SEMICOLON)
            return br

        if self.expect(TokenType.ENTRY, True):
            return ASTEntryPoint()

        if self.expect(TokenType.LEFT_CURL):
            return self.code_block()

        self.error_()

    def return_statement(self):

        expr = self.expression()
        self.match(TokenType.SEMICOLON)
        s = ASTReturnStatement()
        s.add_child(expr)
        return s

    def function_definition(self):
        self.match(TokenType.FUNC)
        ret = self.identifier()
        func_name = self.identifier()
        self.match(TokenType.LEFT_PARENTHESIS)
        arg_list = self.func_arg_list_def()
        self.match(TokenType.RIGHT_PARENTHESIS)

        function_definition_node = ASTFunctionDefinition(None, func_name, ret, arg_list)

        func_body = self.code_block()
        function_definition_node.add_child(func_body)

        return function_definition_node

    def func_arg_list_def(self):
        arg_list = []
        if self.expect(TokenType.ID):
            arg_tuple = self.func_arg()
            arg_list.append(arg_tuple)
            arg_list += self.func_arg_list_def_rest()

        # Do nothing for epsilon production
        return arg_list

    def func_arg_list_def_rest(self):
        out = []
        if self.expect(TokenType.COMMA, True):
            out.append(self.func_arg())
            out += self.func_arg_list_def_rest()

        # Do nothing for epsilon production
        return out

    def func_arg(self):
        arg_type = self.identifier()
        arg_name = self.identifier()
        return arg_type, arg_name

    def if_statement(self):
        self.match(TokenType.IF)
        self.match(TokenType.LEFT_PARENTHESIS)
        cond_expr = self.expression()
        self.match(TokenType.RIGHT_PARENTHESIS)
        body = self.code_block()

        stmt = ASTIfStatement()
        stmt.add_child(cond_expr)
        stmt.add_child(body)
        return stmt

    def while_statement(self):
        self.match(TokenType.WHILE)
        self.match(TokenType.LEFT_PARENTHESIS)
        cond_expr = self.expression()
        self.match(TokenType.RIGHT_PARENTHESIS)
        body = self.code_block()

        w = ASTWhileStatement()
        w.add_child(cond_expr)
        w.add_child(body)
        return w

    def continue_statement(self):
        self.match(TokenType.CONTINUE)
        return ASTContinueStatement()

    def break_statement(self):
        self.match(TokenType.BREAK)
        return ASTBreakStatement()

    def variable_declaration(self):

        self.match(TokenType.VAR)
        tp_node = self.identifier()
        var_node = self.identifier()

        decl_node = ASTDeclaration(tp_node, var_node)

        if self.expect(TokenType.ASSIGN, True):
            expr = self.expression()
            decl_node.add_child(expr)

        return decl_node

    def expression(self):

        return self.assignment_expr()

    def assignment_expr(self):

        cmp_node = self.comparison()
        return self.assignment_expr_rhs(cmp_node)

    def assignment_expr_rhs(self, lhs):

        if self.expect(TokenType.ASSIGN, True):
            rhs = self.comparison()
            node = ASTExpr(TokenType.ASSIGN)
            node.add_child(lhs)
            node.add_child(rhs)
            return self.assignment_expr_rhs(node)

        # Do nothing for epsilon production
        return lhs

    def comparison(self):

        lhs = self.additive_expr()
        return self.comparison_rhs(lhs)

    def comparison_rhs(self, lhs):

        if self.expect_many([TokenType.LE, TokenType.GE, TokenType.EQUAL, TokenType.NOT_EQUAL]):
            op = self.sym().type
            self.advance()
            rhs = self.additive_expr()
            node = ASTExpr(op)
            node.add_child(lhs)
            node.add_child(rhs)
            return self.comparison_rhs(node)

        # Do nothing for epsilon production
        return lhs

    def additive_expr(self):

        lhs = self.multiplicative_expr()
        return self.additive_expr_rhs(lhs)

    def additive_expr_rhs(self, lhs):

        if self.expect(TokenType.PLUS, True):
            rhs = self.multiplicative_expr()
            curr_node = ASTExpr(TokenType.PLUS)
            curr_node.add_child(lhs)
            curr_node.add_child(rhs)
            return self.additive_expr_rhs(curr_node)

        if self.expect(TokenType.MINUS, True):
            rhs = self.multiplicative_expr()
            curr_node = ASTExpr(TokenType.MINUS)
            curr_node.add_child(lhs)
            curr_node.add_child(rhs)
            return self.additive_expr_rhs(curr_node)

        # Do nothing for epsilon production
        return lhs

    def multiplicative_expr(self):

        lhs = self.postfix_expression()
        return self.multiplicative_expr_rhs(lhs)

    def multiplicative_expr_rhs(self, lhs):

        if self.expect(TokenType.MUL, True):
            rhs = self.postfix_expression()
            curr_node = ASTExpr(TokenType.MUL)
            curr_node.add_child(lhs)
            curr_node.add_child(rhs)
            return self.multiplicative_expr_rhs(curr_node)

        if self.expect(TokenType.DIV, True):
            rhs = self.postfix_expression()
            curr_node = ASTExpr(TokenType.DIV)
            curr_node.add_child(lhs)
            curr_node.add_child(rhs)
            return self.multiplicative_expr_rhs(curr_node)

        # Do nothing for epsilon production
        return lhs

    def postfix_expression(self):

        print('In postfix_expression: curr token: ', self.sym())

        lhs = self.primary_expression()
        return self.postfix_expression_rest(lhs)

    def func_call_arg_list(self):

        nodes = []
        # FIRST(expression)
        if self.expect_many([TokenType.ID, TokenType.LEFT_PARENTHESIS, TokenType.NUM]):
            expr = self.expression()
            nodes.append(expr)
            nodes += self.func_call_arg_list_rest()
        return nodes

    def func_call_arg_list_rest(self):

        nodes = []
        if self.expect(TokenType.COMMA, True):
            expr = self.expression()
            nodes.append(expr)
            nodes += self.func_call_arg_list_rest()
        return nodes

    def postfix_expression_rest(self, lhs):

        if self.expect(TokenType.LEFT_PARENTHESIS, True):

            arg_list = self.func_call_arg_list()
            for arg in arg_list:
                lhs.add_child(arg)

            self.match(TokenType.RIGHT_PARENTHESIS)
            return lhs

        if self.expect(TokenType.LEFT_BRACKET):
            raise NotImplementedError('Array subscript not implemented')

            # TODO: arrays?
            # self.match(TokenType.LEFT_BRACKET)

        # Do nothing for epsilon production
        return lhs

    def primary_expression(self):

        s = self.sym()
        print('In primary_expression: current token:%s' % str(s))

        if self.expect(TokenType.NUM, True):
            print('Number')
            return ASTNumber(s.value)

        if self.expect(TokenType.ID, True):
            print('Identifier')

            if self.expect(TokenType.LEFT_PARENTHESIS):
                return ASTFunctionCall(None, s.lexeme)

            return ASTId(None, s.lexeme)

        self.match(TokenType.LEFT_PARENTHESIS)
        curr_node = self.expression()
        self.match(TokenType.RIGHT_PARENTHESIS)

        return curr_node

    def identifier(self):
        node = ASTId(None, self.sym().lexeme)
        self.advance()
        return node


if __name__ == '__main__':

    def read_code(file_path):
        with open(file_path, 'r') as f:
            return f.read()

    from my_lexer import Lexer
    code = read_code('parsing_test_data/function_without_return.prog')
    lex = Lexer()
    tokens = lex.analyze(code)
    parser = NewParser()
    ast = parser.parse(tokens)
    visitor = PrintVisitor()
    ast.accept(visitor)
