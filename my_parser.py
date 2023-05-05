from symbol_table import Symbol, SymbolTable, SymbolType, SymbolFunction, SymbolId

from my_lexer import TokenType

from my_ast import ASTDeclaration, ASTExpr, ASTId, ASTNumber, ASTCodeBlock, ASTFunctionDefinition, ASTIfStatement, \
    ASTWhileStatement, ASTBreakStatement, ASTContinueStatement, ASTReturnStatement, ASTFunctionCall, ASTEntryPoint

from my_ast import print_ast

from errors import UnexpectedTokenError, CompileError

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


class Parser:

    def __init__(self, tokens=None):
        self.curr_sym = None
        self.idx = -1

        self.tokens = tokens
        if tokens is None:
            self.tokens = []
        self.num_tokens = len(self.tokens)

        self.curr_label_id = 0

        self.advance()

        self.root = None

        self.symtable = SymbolTable()

        self.init_types()

    def init_types(self):

        self.symtable.add(SymbolType('int', 1))
        self.symtable.add(SymbolType('float', 1))

    def error_(self):
        raise UnexpectedTokenError(self.sym(), self.idx)
        # raise SyntaxError('Unexpected token %s at position %d' % (self.sym(),self.idx))

    def eof(self):
        return self.idx == self.num_tokens

    def sym(self):
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
        return True

    def program(self):

        node = self.code_block()

        if not self.eof():
            self.error_()

        return node

    def code_block(self):

        self.match(TokenType.LEFT_CURL)

        self.symtable = SymbolTable(self.symtable)
        print('Code block table:')
        print(self.symtable.show())
        stmt_nodes = self.statement_list()

        curr_node = ASTCodeBlock(self.symtable)
        for stmt in stmt_nodes:
            curr_node.add_child(stmt)

        if self.symtable.parent:
            self.symtable = self.symtable.parent

        self.match(TokenType.RIGHT_CURL)

        return curr_node

    def statement_list(self):

        # FIRST(statement)
        possible_tokens = [TokenType.LEFT_PARENTHESIS,
                           TokenType.VAR, TokenType.FUNC, TokenType.RETURN, TokenType.IF, TokenType.LEFT_CURL,
                           TokenType.ID, TokenType.WHILE, TokenType.CONTINUE, TokenType.BREAK,
                           TokenType.NUM, TokenType.ENTRY]

        print('Current symbol:', self.sym())
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
        ret_type = self.identifier_type()
        func_name = self.get_name()
        self.match(TokenType.LEFT_PARENTHESIS)
        arg_list = self.func_arg_list_def()
        self.match(TokenType.RIGHT_PARENTHESIS)

        _func = SymbolFunction(func_name, ret_type, arg_list)
        f_sym = self.symtable.add(_func)

        f = ASTFunctionDefinition(f_sym, func_name, ret_type, arg_list)
        f.symtable = SymbolTable(self.symtable)
        self.symtable = f.symtable

        for tp, name in arg_list:
            var = SymbolId(name, tp, None)
            f.symtable.add(var)

        func_body = self.code_block()
        f.add_child(func_body)

        self.symtable = self.symtable.parent

        return f

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
            # TODO: function calls?
            self.func_arg()
            out += self.func_arg_list_def_rest()

        # Do nothing for epsilon production
        return out

    def func_arg(self):

        arg_type = self.identifier_type()
        arg_name = self.get_name()
        return arg_type, arg_name

    def if_statement(self):
        self.match(TokenType.IF)
        self.match(TokenType.LEFT_PARENTHESIS)
        cond_expr = self.expression()
        self.match(TokenType.RIGHT_PARENTHESIS)
        body = self.code_block()

        self.curr_label_id += 1
        stmt = ASTIfStatement(self.curr_label_id)
        stmt.add_child(cond_expr)
        stmt.add_child(body)
        return stmt

    def while_statement(self):
        self.match(TokenType.WHILE)
        self.match(TokenType.LEFT_PARENTHESIS)
        cond_expr = self.expression()
        self.match(TokenType.RIGHT_PARENTHESIS)
        body = self.code_block()

        self.curr_label_id += 1
        w = ASTWhileStatement(self.curr_label_id)
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
        tp_node = self.identifier_type()
        var_node = self.identifier_var(tp_node)

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

        print('In postfix_expression: curr token=', self.sym())

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
            print('Identifier', s.lexeme)
            var_entry = self.symtable.find(s.lexeme)
            print(s, var_entry)
            is_id_or_func = var_entry.symbol_type in [Symbol.Id, Symbol.Function]
            if var_entry is None or not is_id_or_func:
                raise ValueError('Undeclared identifier:', s.lexeme)
            if self.expect(TokenType.LEFT_PARENTHESIS):
                if var_entry.symbol_type != Symbol.Function:
                    raise CompileError(f'Expected function call, but got different kind of symbol: {var_entry}')
                return ASTFunctionCall(var_entry, s.lexeme)

            return ASTId(var_entry, s.lexeme)

        self.match(TokenType.LEFT_PARENTHESIS)
        curr_node = self.expression()
        self.match(TokenType.RIGHT_PARENTHESIS)

        return curr_node

    def get_name(self):
        n = self.sym().lexeme
        _s = self.symtable.find(n)
        if _s:
            raise CompileError(f'Symbol with name {n} already exists: {_s}')
        self.advance()
        return n

    def identifier_type(self):

        tp_name = self.sym().lexeme

        tp_entry = self.symtable.find(tp_name)
        if tp_entry is None or tp_entry.symbol_type != Symbol.Type:
            raise ValueError('%s does not name a type' % tp_name)

        self.advance()

        return tp_entry

    def identifier_var(self, tp):
        var_name = self.sym().lexeme
        print('Variable name: "%s"' % var_name)
        print(tp)

        var_entry = self.symtable.add(SymbolId(var_name, tp, None))
        self.advance()

        return var_entry
