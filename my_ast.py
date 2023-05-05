from my_lexer import TokenType
from errors import CompileError, InvalidReturnError, LoopError
from ast_node import ASTNode
from ast_visitor import AstVisitor


def find_parent_node(node, tp_list):

    tp_list = [tp.__name__ for tp in tp_list]

    curr = node.parent

    while curr is not None:
        if curr.__class__.__name__ in tp_list:
            return curr
        curr = curr.parent
    return None


def find_parent_node_one_type(node, tp):
    return find_parent_node(node, [tp])


class ASTExpr(ASTNode):

    def __init__(self, op, parent=None):
        super().__init__(parent)
        self.op = op

    def accept(self, v: AstVisitor):
        v.visit_expr(self)

    def emit(self):

        print('Expression', self.op)
        binary_op_map = {TokenType.PLUS: 'add', TokenType.MINUS: 'sub', TokenType.MUL: 'mul', TokenType.DIV: 'div',
                         TokenType.LE: 'lt', TokenType.GE: 'gt', TokenType.EQUAL: 'eq', TokenType.NOT_EQUAL: 'neq'}

        if self.op in binary_op_map:
            get_op1 = self.children[0].emit()
            get_op2 = self.children[1].emit()
            return get_op1 + get_op2 + [binary_op_map[self.op]]

        if self.op == TokenType.ASSIGN:
            addr = self.children[0].symbol.address
            calc_rhs = self.children[1].emit()
            return calc_rhs + ['store %d' % addr]


class ASTEntryPoint(ASTNode):
    def __init__(self, parent=None):
        super().__init__(parent)

    def accept(self, v: AstVisitor):
        v.visit_entry_point(self)

    def emit(self):
        return ['program:']


class ASTNumber(ASTNode):
    def __init__(self, value, parent=None):
        super().__init__(parent)

        self.value = value

    def accept(self, v: AstVisitor):
        v.visit_num(self)

    def emit(self):
        out = ['push %d' % self.value]
        return out


class ASTId(ASTNode):
    def __init__(self, symbol, name, parent=None):
        super().__init__(parent)

        self.symbol = symbol
        self.name = name

    def accept(self, v: AstVisitor):
        v.visit_id(self)

    def emit(self):
        addr = self.symbol.address
        return ['load %d' % addr]


class ASTDeclaration(ASTNode):
    def __init__(self, tp_sym, var_sym, parent=None):
        super().__init__(parent)

        self.tp = tp_sym
        self.name = var_sym

    def accept(self, v: AstVisitor):
        v.visit_declaration(self)

    def emit(self):
        out = ['push %d' % self.tp.size, 'alloc']

        self.name.address = self.parent.curr_mem_idx
        self.parent.curr_mem_idx += self.tp.size
        self.parent.memory_size += self.tp.size

        if len(self.children) > 0:
            out += self.children[0].emit()
            out.append('store %d' % self.name.address)

        return out


class ASTIfStatement(ASTNode):
    def __init__(self, label_id=None, parent=None):
        super().__init__(parent)

        self.label_id = label_id

    def accept(self, v: AstVisitor):
        v.visit_if(self)

    def emit(self):
        out = []
        if len(self.children) < 2:
            raise CompileError('Too few children for `if` statement')

        condition = self.children[0]
        body = self.children[1]

        cond_cmd = condition.emit()
        body_cmd = body.emit()

        after_label = '_if%d' % self.label_id
        out += cond_cmd
        out.append('jz %s' % after_label)
        out += body_cmd
        out.append(after_label + ':')
        return out


class ASTWhileStatement(ASTNode):
    def __init__(self, label_id=None, parent=None):
        super().__init__(parent)

        self.label_id = label_id

        self.cond_check_label = f'_while_cond{self.label_id}'
        self.after_label = f'_while_after{self.label_id}'

    def accept(self, v: AstVisitor):
        v.visit_while(self)

    def emit(self):
        out = []
        if len(self.children) < 2:
            raise CompileError('Too few children for `while` statement')

        condition = self.children[0]
        body = self.children[1]

        cond_cmd = condition.emit()
        body_cmd = body.emit()

        out.append(self.cond_check_label + ':')
        out += cond_cmd
        out.append('jz %s' % self.after_label)
        out += body_cmd
        out.append('jump %s' % self.cond_check_label)
        out.append(self.after_label + ':')
        return out


class ASTContinueStatement(ASTNode):
    def __init__(self, parent=None):
        super().__init__(parent)

    def accept(self, v: AstVisitor):
        v.visit_continue(self)

    def emit(self):
        loop_node = find_parent_node_one_type(self, ASTWhileStatement)
        if not loop_node:
            raise LoopError(self.__class__.__name__, 0)

        cond_check_label = loop_node.cond_check_label

        return ['jump %s' % cond_check_label]


class ASTBreakStatement(ASTNode):
    def __init__(self, parent=None):
        super().__init__(parent)

    def accept(self, v: AstVisitor):
        v.visit_break(self)

    def emit(self):
        loop_node = find_parent_node_one_type(self, ASTWhileStatement)
        if not loop_node:
            raise LoopError(self.__class__.__name__, 0)

        after_label = loop_node.after_label

        return ['jump %s' % after_label]


class ASTCodeBlock(ASTNode):
    def __init__(self, symtable=None, parent=None):
        super().__init__(parent)

        self.symtable = symtable

        self.curr_mem_idx = 0
        self.memory_size = 0

    def accept(self, v: AstVisitor):
        v.visit_code_block(self)

    def emit(self):

        out = []

        parent_code_block = find_parent_node(self, [ASTCodeBlock, ASTFunctionDefinition])
        if parent_code_block:
            self.curr_mem_idx = parent_code_block.curr_mem_idx

        for node in self.children:
            cmd_list = node.emit()
            out += cmd_list

        out.append('push %d' % self.memory_size)
        out.append('dealloc')

        return out


class ASTReturnStatement(ASTNode):
    def __init__(self, parent=None):
        super().__init__(parent)

    def accept(self, v: AstVisitor):
        v.visit_return(self)

    def emit(self):
        p = find_parent_node_one_type(self, ASTFunctionDefinition)
        if p is None:
            raise InvalidReturnError()
        expr = self.children[0]
        out = expr.emit()
        out.append('ret')
        return out


class ASTFunctionDefinition(ASTNode):
    def __init__(self, func_symbol, func_name, ret_type, args, parent=None):
        super().__init__(parent)

        self.func_symbol = func_symbol
        self.func_name = func_name
        self.ret_type = ret_type
        self.args = args

        self.total_args_size = self.func_symbol.args_size if self.func_symbol else 0
        print('Total args size:', self.total_args_size)

        self.curr_mem_idx = 0
        self.memory_size = 0

        self.symtable = None

    def accept(self, v: AstVisitor):
        v.visit_function_definition(self)

    def emit(self):
        out = []

        if len(self.children) < 1 or not isinstance(self.children[0], ASTCodeBlock):
            raise ValueError('No code block for function:', self.func_symbol.name)

        body = self.children[0]

        for tp, name in self.func_symbol.args:
            var = self.symtable.find(name)
            var.address = self.curr_mem_idx
            self.curr_mem_idx += tp.size
            self.memory_size += tp.size

        label = self.func_symbol.label
        out.append(label + ':')
        for tp, name in self.func_symbol.args[::-1]:
            var = self.symtable.find(name)
            out.append('push %d' % var.type.size)
            out.append('alloc')
            out.append('store %d' % var.address)

        body_cmd = body.emit()

        out += body_cmd

        out.append('ret')

        return out


class ASTFunctionCall(ASTNode):
    def __init__(self, func_symbol, func_name, parent=None):
        super().__init__(parent)

        self.func_symbol = func_symbol
        self.func_name = func_name

    def accept(self, v: AstVisitor):
        v.visit_function_call(self)

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


def print_ast(root, lvl=0):
    prefix = '    ' * lvl
    print(prefix + '{')

    print(prefix + ' Type:', root.__class__.__name__)

    if root.__class__ == ASTDeclaration:
        print(prefix + ' var_type:', root.tp)
        print(prefix + ' var_name:', root.name)
    if root.__class__ == ASTCodeBlock:
        if root.symtable:
            print(prefix + ' SymbolTable:')
            print(root.symtable.show(prefix + '  '))

    if hasattr(root, 'value'):
        print(prefix + ' Value:', root.value)
    if hasattr(root, 'symbol'):
        print(prefix + ' Symbol:', root.symbol)

    print(prefix + ' Children:')

    for ch in root.children:
        print_ast(ch, lvl + 1)

    print(prefix + '}')
