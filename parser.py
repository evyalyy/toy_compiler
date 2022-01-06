from symbol_table import *

from lexer import Lexer

class CompileError(Exception):
    def __init__(self,msg):
        self.msg = msg
    
    def __str__(self):
        return self.msg

class InvalidReturError(CompileError):
    def __init__(self):
        pass

    def __str__(self):
        return 'Return statement outside function definition'

class UnexpectedTokenError(CompileError):

    def __init__(self,tok,pos):

        self.tok = tok
        self.pos = pos

    def __str__(self):

        return 'Unexpected token <%s> at position %d' % (self.tok,self.pos)

class LoopError(CompileError):

    def __init__(self,name,pos):

        self.pos = pos
        self.name = name

    def __str__(self):
        msg = '<%s> statement at pos %d is outside a loop' % (self.name,self.pos)
        return msg

class ASTNode(object):

    def __init__(self,tp,parent = None):

        self.type = tp

        self.parent = parent
        self.children = []

    def addChildLeft(self,node):
        node.parent = self
        self.children.insert(0,node)

    def addChild(self,node):
        node.parent = self
        self.children.append(node)

    def emit(self):
        raise NotImplementedError()

def find_parent_node(node,tp_list):
    if isinstance(tp_list,str):
        tp_list = [tp_list]

    curr = node.parent

    while curr is not None:
        if curr.type in tp_list:
            return curr
        curr = curr.parent
    return None

class ASTExpr(ASTNode):

    def __init__(self,op,parent = None):
        super(ASTExpr,self).__init__(op,parent)
        self.op = op

    def emit(self):

        print('Expression',self.op)
        binary_op_map = {'plus':'add','minus':'sub','multiply':'mul','divide':'div'}
        binary_op_map['less'] = 'lt'
        binary_op_map['greater'] = 'gt'
        binary_op_map['equal'] = 'eq'
        binary_op_map['notequal'] = 'neq'

        if self.op in binary_op_map:
            get_op1 = self.children[0].emit()
            get_op2 = self.children[1].emit()
            return get_op1 + get_op2 + [binary_op_map[self.op]]

        if self.op == 'assign':
            addr = self.children[0].symbol.address
            calc_rhs = self.children[1].emit()
            return calc_rhs + ['store %d' % addr]

class ASTEntryPoint(ASTNode):
    def __init__(self,parent=None):
        super().__init__('entry',parent)

    def emit(self):

        return ['program:']

class ASTNumber(ASTNode):
    def __init__(self,value,parent = None):
        super(ASTNumber,self).__init__('number',parent)

        self.value = value

    def emit(self):

        out = ['push %d' % self.value]
        return out

class ASTId(ASTNode):
    def __init__(self,symbol,parent=None):
        super(ASTId,self).__init__('id',parent)

        self.symbol = symbol

    def emit(self):

        addr = self.symbol.address
        return ['load %d' % addr]

class ASTDeclaration(ASTNode):
    def __init__(self,tp_sym,var_sym,parent=None):
        super(ASTDeclaration,self).__init__('declaration',parent)

        self.tp = tp_sym
        self.name = var_sym

    def emit(self):

        out = []
        out.append('push %d' % self.tp.size)
        out.append('alloc')

        self.name.address = self.parent.curr_mem_idx
        self.parent.curr_mem_idx += self.tp.size
        self.parent.memsize += self.tp.size

        if len(self.children) > 0:
            out += self.children[0].emit()
            out.append('store %d' % self.name.address)

        return out

class ASTIfStatement(ASTNode):
    def __init__(self,label_id,parent=None):
        super(ASTIfStatement,self).__init__('if',parent)

        self.label_id = label_id

    def emit(self):

        out = []
        if len(self.children) > 1:
            condition = self.children[0]
            body = self.children[1]

        cond_cmd = condition.emit()
        body_cmd = body.emit()

        after_label = '_if%d' % self.label_id
        out += cond_cmd
        out.append('jz %s' % after_label)
        out += body_cmd
        out.append(after_label+':')
        return out


class ASTWhileStatement(ASTNode):
    def __init__(self,label_id,parent=None):
        super(ASTWhileStatement,self).__init__('while',parent)

        self.label_id = label_id

        self.cond_check_label = '_while_cond%d' % self.label_id
        self.after_label = '_while_after%d' % self.label_id

    def emit(self):

        out = []
        if len(self.children) > 1:
            condition = self.children[0]
            body = self.children[1]

        cond_cmd = condition.emit()
        body_cmd = body.emit()

        out.append(self.cond_check_label+':')
        out += cond_cmd
        out.append('jz %s' % self.after_label)
        out += body_cmd
        out.append('jump %s' % self.cond_check_label)
        out.append(self.after_label+':')
        return out

class ASTContinueStatement(ASTNode):
    def __init__(self,parent=None):
        super(ASTContinueStatement,self).__init__('continue',parent)

    def emit(self):

        loop_node = find_parent_node(self,'while')
        if not loop_node:
            raise LoopError(self.type,0)

        cond_check_label = loop_node.cond_check_label

        return ['jump %s' % cond_check_label]

class ASTBreakStatement(ASTNode):
    def __init__(self,parent=None):
        super(ASTBreakStatement,self).__init__('break',parent)

    def emit(self):

        loop_node = find_parent_node(self,'while')
        if not loop_node:
            raise LoopError(self.type,0)
        
        after_label = loop_node.after_label

        return ['jump %s' % after_label]

class ASTCodeBlock(ASTNode):
    def __init__(self,symtable,parent=None):
        super(ASTCodeBlock,self).__init__('code_block',parent)

        self.symtable = symtable

        self.curr_mem_idx = 0
        self.memsize = 0
    
    def emit(self):

        out = []

        parent_code_block = find_parent_node(self,['code_block','function_definition'])
        if parent_code_block:
            self.curr_mem_idx = parent_code_block.curr_mem_idx

        for node in self.children:

            cmd_list = node.emit()
            out += cmd_list

        out.append('push %d' % self.memsize)
        out.append('dealloc')

        return out

class ASTReturnStatement(ASTNode):
    def __init__(self,parent=None):
        super().__init__('return',parent)

    def emit(self):

        p = find_parent_node(self,'function_definition')
        if p is None:
            raise InvalidReturError()
        expr = self.children[0]
        out = expr.emit()
        out.append('ret')
        return out

class ASTFunctionDefinition(ASTNode):
    def __init__(self,func_symbol,parent=None):
        super().__init__('function_definition',parent)

        self.func_symbol = func_symbol

        self.total_args_size = self.func_symbol.args_size
        print('Total args size:',self.total_args_size)

        self.curr_mem_idx = 0
        self.memsize = 0

        self.symtable = None

    def emit(self):
        out = []

        if len(self.children) < 1 or self.children[0].type != 'code_block':
            raise ValueError('No code block for function:',self.func_symbol.name)

        body = self.children[0]

        for tp,name in self.func_symbol.args:
            var = self.symtable.find(name)
            var.address = self.curr_mem_idx
            self.curr_mem_idx += tp.size
            self.memsize += tp.size

        label = self.func_symbol.label
        out.append(label+':')
        for tp,name in self.func_symbol.args[::-1]:
            var = self.symtable.find(name)
            out.append('push %d' % var.type.size)
            out.append('alloc')
            out.append('store %d' % var.address)

        body_cmd = body.emit()

        out += body_cmd

        out.append('ret')

        return out

class ASTFunctionCall(ASTNode):
    def __init__(self,func_symbol,parent=None):
        super().__init__('function_call',parent)

        self.func_symbol = func_symbol

    def emit(self):
        out = []
        n_args = len(self.children)
        if n_args != len(self.func_symbol.args):
            raise CompileError('Invalid arity in call to %s' % self.func_symbol.name)

        for ch in self.children:
            cmd = ch.emit()
            out += cmd
        out.append('push %d' % n_args)
        out.append('call %s' % self.func_symbol.label)
        return out

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

def print_ast(root,lvl = 0):

    prefix = '    '*lvl
    print(prefix+'{')

    print(prefix+' Type:',root.type)

    if root.type == 'declaration':
        print(prefix+' var_type:',root.tp)
        print(prefix+' var_name:',root.name)
    if root.type == 'code_block':
        print(prefix+' SymbolTable:')
        print(root.symtable.show(prefix+'  '))
    
    if hasattr(root,'value'):
        print(prefix+' Value:',root.value)
    if hasattr(root,'symbol'):
        print(prefix+' Symbol:',root.symbol)

    print(prefix+' Children:')

    for ch in root.children:
        print_ast(ch,lvl+1)

    print(prefix+'}')
    
    


class Parser:

    def __init__(self,tokens=[]):
        self.curr_sym = None
        self.idx = -1

        self.tokens = tokens
        self.ntokens = len(self.tokens)

        self.curr_label_id = 0

        self.advance()
        
        self.root = None

        self.symtable = SymbolTable()

        self.init_types()

    def init_types(self):

        self.symtable.add(SymbolType('int',1))
        self.symtable.add(SymbolType('float',1))

    def error_(self):
        raise UnexpectedTokenError(self.sym(),self.idx)
        # raise SyntaxError('Unexpected token %s at position %d' % (self.sym(),self.idx))

    def eof(self):
        return self.idx == self.ntokens

    def sym(self):
        return self.curr_sym


    def expect(self,tp,match=False):
        s = self.sym()
        if tp != s.type:
            return False

        if match:
            self.match(tp)
        return True

    def expect_many(self,tps):

        for s in tps:
            if self.expect(s):
                return True
        return False

    def match(self,tp):
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

        self.match('lcurv')

        self.symtable = SymbolTable(self.symtable)
        print('Code block table:')
        print(self.symtable.show())
        stmt_nodes = self.statement_list()

        curr_node = ASTCodeBlock(self.symtable)
        for stmt in stmt_nodes:
            curr_node.addChild(stmt)

        if self.symtable.parent:
            self.symtable = self.symtable.parent

        self.match('rcurv')

        return curr_node

    def statement_list(self):

        # FIRST(statement)
        possible_toks = ['lparen','var','func','return','if','lcurv',\
                         'id','while','continue','break','number','entry']
        
        print('Current symbol:',self.sym())
        nodes = []
        if self.expect_many(possible_toks):

            curr_node = self.statement()

            nodes.append(curr_node)
            nodes += self.statement_list()

        # Do nothing for epsilon production
        return nodes

    def statement(self):

        if self.expect('var'):
            dec = self.variable_declaration()
            self.match('semicolon')
            return dec

        if self.expect('func'):
            func_def = self.function_definition()
            return func_def

        if self.expect('return',True):
            return self.return_statement()

        # expecting symbol from FIRST(expression)
        if self.expect_many(['id','lparen','number']):
            expr = self.expression()
            self.match('semicolon')
            return expr

        if self.expect('if'):
            print('IF statement')
            return self.if_statement()

        if self.expect('while'):
            print('WHILE statement')
            return self.while_statement()

        if self.expect('continue'):
            print('Continue')
            cont = self.continue_statement()
            self.match('semicolon')
            return cont

        if self.expect('break'):
            print('Break')
            br = self.break_statement()
            self.match('semicolon')
            return br

        if self.expect('entry',True):
            return ASTEntryPoint()

        if self.expect('lcurv'):
            return self.code_block()

        self.error_()

    def return_statement(self):

        expr = self.expression()
        self.match('semicolon')
        s = ASTReturnStatement()
        s.addChild(expr)
        return s


    def function_definition(self):
        self.match('func')
        ret_type = self.identifierType()
        func_name = self.getName()
        self.match('lparen')
        arg_list = self.func_arg_list_def()
        self.match('rparen')
        
        _func = SymbolFunction(func_name,ret_type,arg_list)
        f_sym = self.symtable.add(_func)
        
        f = ASTFunctionDefinition(f_sym)
        f.symtable = SymbolTable(self.symtable)
        self.symtable = f.symtable

        for tp,name in arg_list:
            var = SymbolId(name,tp,None)
            f.symtable.add(var)
        
        func_body = self.code_block()
        f.addChild(func_body)
        
        self.symtable = self.symtable.parent
        
        return f

    def func_arg_list_def(self):
        arg_list = []
        if self.expect('id'):
            arg_tuple = self.func_arg()
            arg_list.append(arg_tuple)
            arg_list += self.func_arg_list_def_rest()

        # Do nothing for epsilon production
        return arg_list


    def func_arg_list_def_rest(self):
        out = []
        if self.expect('comma',True):
            arg_tuple = self.func_arg()
            out += self.func_arg_list_def_rest()

        # Do nothing for epsilon production
        return out

    def func_arg(self):

        arg_type = self.identifierType()
        arg_name = self.getName()
        return (arg_type,arg_name)

    def if_statement(self):
        self.match('if')
        self.match('lparen')
        cond_expr = self.expression()
        self.match('rparen')
        body = self.code_block()

        self.curr_label_id += 1
        stmt =  ASTIfStatement(self.curr_label_id)
        stmt.addChild(cond_expr)
        stmt.addChild(body)
        return stmt

    def while_statement(self):
        self.match('while')
        self.match('lparen')
        cond_expr = self.expression()
        self.match('rparen')
        body = self.code_block()

        self.curr_label_id += 1
        w = ASTWhileStatement(self.curr_label_id)
        w.addChild(cond_expr)
        w.addChild(body)
        return w

    def continue_statement(self):
        self.match('continue')
        return ASTContinueStatement()

    def break_statement(self):
        self.match('break')
        return ASTBreakStatement()

    def variable_declaration(self):

        self.match('var')
        tp_node = self.identifierType()
        var_node = self.identifierVar(tp_node)

        decl_node = ASTDeclaration(tp_node,var_node)

        if self.expect('assign',True):
            expr = self.expression()
            decl_node.addChild(expr)

        return decl_node

    def expression(self):

        return self.assignment_expr()

    def assignment_expr(self):

        cmp_node = self.comparison()
        return self.assignment_expr_rhs(cmp_node)

    def assignment_expr_rhs(self,lhs):

        if self.expect('assign',True):
            rhs = self.comparison()
            node = ASTExpr('assign')
            node.addChild(lhs)
            node.addChild(rhs)
            return self.assignment_expr_rhs(node)
        
        # Do nothing for epsilon production
        return lhs

    def comparison(self):

        lhs = self.additive_expr()
        return self.comparison_rhs(lhs)

    def comparison_rhs(self,lhs):

        if self.expect_many(['less','greater','equal','notequal']):
            op = self.sym().type
            self.advance()
            rhs = self.additive_expr()
            node = ASTExpr(op)
            node.addChild(lhs)
            node.addChild(rhs)
            return self.comparison_rhs(node)

        # Do nothing for epsilon production
        return lhs

    def additive_expr(self):

        lhs = self.multiplicative_expr()
        return self.additive_expr_rhs(lhs)

    def additive_expr_rhs(self,lhs):

        if self.expect('plus',True):
            rhs = self.multiplicative_expr()
            curr_node = ASTExpr('plus')
            curr_node.addChild(lhs)
            curr_node.addChild(rhs)
            return self.additive_expr_rhs(curr_node)

        if self.expect('minus',True):
            rhs = self.multiplicative_expr()
            curr_node = ASTExpr('minus')
            curr_node.addChild(lhs)
            curr_node.addChild(rhs)
            return self.additive_expr_rhs(curr_node)

        # Do nothing for epsilon production
        return lhs

    def multiplicative_expr(self):

        lhs = self.postfix_expression()
        return self.multiplicative_expr_rhs(lhs)

    def multiplicative_expr_rhs(self,lhs):

        if self.expect('multiply',True):
            rhs = self.postfix_expression()
            curr_node = ASTExpr('multiply')
            curr_node.addChild(lhs)
            curr_node.addChild(rhs)
            return self.multiplicative_expr_rhs(curr_node)

        if self.expect('divide',True):
            rhs = self.postfix_expression()
            curr_node = ASTExpr('divide')
            curr_node.addChild(lhs)
            curr_node.addChild(rhs)
            return self.multiplicative_expr_rhs(curr_node)

        # Do nothing for epsilon production
        return lhs

    def postfix_expression(self):

        print('In postfix_expression: curr token=',self.sym())

        lhs = self.primary_expression()
        return self.postfix_expression_rest(lhs)

    def func_call_arg_list(self):

        nodes = []
        # FIRST(expression)
        if self.expect_many(['id','lparen','number']):
            expr = self.expression()
            nodes.append(expr)
            nodes += self.func_call_arg_list_rest()
        return nodes

    def func_call_arg_list_rest(self):

        nodes = []
        if self.expect('comma',True):
            expr = self.expression()
            nodes.append(expr)
            nodes += self.func_call_arg_list_rest()
        return nodes

    def postfix_expression_rest(self,lhs):

        if self.expect('lparen',True):

            arg_list = self.func_call_arg_list()
            for arg in arg_list:
                lhs.addChild(arg)

            self.match('rparen')
            return lhs

        if self.expect('lsquare'):

            raise NotImplementedError('Array subscript not implemented')

            self.match('rsquare')

        # Do nothing for epsilon production
        return lhs

    def primary_expression(self):
        
        s = self.sym()
        print('In primary_expression: current token:%s' % str(s))

        if self.expect('number',True):
            print('Number')
            return ASTNumber(s.value)

        if self.expect('id',True):
            print('Identifier')
            var_entry = self.symtable.find(s.lexeme)
            print(s,var_entry)
            is_id_or_func = var_entry.symbol_type in [Symbol.Id,Symbol.Function]
            if var_entry is None or not is_id_or_func:
                raise ValueError('Undeclared identifier:',s.lexeme)

            if var_entry.symbol_type == Symbol.Id:
                return ASTId(var_entry)

            if var_entry.symbol_type == Symbol.Function:
                return ASTFunctionCall(var_entry)

        self.match('lparen')
        curr_node = self.expression()
        self.match('rparen')

        return curr_node

    def getName(self):
        '''
        TODO: add check that there is no type with such name (or variable, or function)
        '''
        n = self.sym().lexeme
        _s = self.symtable.find(n)
        if _s:
            raise ValueError('There is a symbol with such name:',_s)
        self.advance()
        return n


    def identifierType(self):

        tp_name = self.sym().lexeme

        tp_entry = self.symtable.find(tp_name)
        if tp_entry is None or tp_entry.symbol_type != Symbol.Type:
            raise ValueError('%s does not name a type' % tp_name)

        self.advance()

        return tp_entry
    
    def identifierVar(self,tp):
        var_name = self.sym().lexeme
        print('Variable name: "%s"' % var_name)
        print(tp)

        var_entry = self.symtable.add(SymbolId(var_name,tp,None))
        self.advance()

        return var_entry

from virtual_machine import VirtualMachine


if __name__ == '__main__':
    

    code = '''
    {
       func int foo(int x){
            var int tmp = 0;
            var int y = 10;
            tmp = x + y;
            if(tmp < 50){
                tmp = foo(tmp);
            }
            return tmp;
       }
       entry
       foo(1);
       //func int bar(){
       // var float x = 0;
       //}
        # var int n = 9;
        # var int prev1 = 1;
        # var int prev2 = 1;
        # while(n > 2){
        #     var int tmp = prev1;
        #     prev1 = prev1 + prev2;
        #     prev2 = tmp;
        #     n = n - 1;
        # }

       # var int n = 5;
       # var int result = 1;
       # while(n > 0){
       #      result = result * n;
       #      n = n - 1;
       # }
    }
    '''

    lex = Lexer() 
    tokens = lex.analyze(code)

    print('Parsing')
    pr = Parser(tokens)
    ast = pr.program()

    print_ast(ast)

    cmd_list = ast.emit()

    code = ';\n'.join(cmd_list) + ';\nhalt;'
    code = code.replace(':;',':')
    print(code)

    vm = VirtualMachine()
    vm.run_code(code)
    vm.show(2)