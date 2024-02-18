from ast_visitor import AstVisitor
from symbol_table import SymbolTable
from errors import UndeclaredTypeError, RedefinitionError
from symbol_table import SymbolType, SymbolId
from my_token import TokenType


class CodegenVisitor(AstVisitor):
    def __init__(self):
        self.symbol_table = SymbolTable()
        self.symbol_table.add(SymbolType('int', 1))
        self.symbol_table.add(SymbolType('float', 1))
        self.current_relative_address = 0
        self.current_memory_size = 0
        self.current_label_id = 0
        self.bytecode = []

    def get_next_label_id(self):
        self.current_label_id += 1
        return self.current_label_id

    def visit_id(self, node):
        var_address = self.symbol_table.find(node.name).address
        self.bytecode.append(f'load {var_address}')

    def visit_num(self, node):
        self.bytecode.append(f'push {node.value}')

    def visit_expr(self, node):
        binary_op_map = {TokenType.PLUS: 'add', TokenType.MINUS: 'sub', TokenType.MUL: 'mul', TokenType.DIV: 'div',
                         TokenType.LE: 'lt', TokenType.GE: 'gt', TokenType.EQUAL: 'eq', TokenType.NOT_EQUAL: 'neq'}

        if node.op in binary_op_map:
            node.children[0].accept(self)
            node.children[1].accept(self)
            self.bytecode.append(binary_op_map[node.op])

        if node.op == TokenType.ASSIGN:
            lvalue_address = self.symbol_table.find(node.children[0].name).address
            node.children[1].accept(self)
            self.bytecode.append(f'store {lvalue_address}')

    def visit_entry_point(self, node):
        self.bytecode.append('program:')

    def visit_declaration(self, node):
        type_name = node.tp.name
        var_name = node.name.name

        type_symbol = self.symbol_table.find(type_name)
        if type_symbol is None:
            raise UndeclaredTypeError(type_name)

        if self.symbol_table.find_at_current_level(var_name):
            raise RedefinitionError(var_name)

        new_symbol = self.symbol_table.add(SymbolId(var_name, type_name, self.current_relative_address))
        self.current_relative_address += 1
        self.current_memory_size += 1

        self.bytecode.extend(['push 1', 'alloc'])

        if len(node.children) == 1:
            node.children[0].accept(self)
            self.bytecode.append(f'store {new_symbol.address}')

    def visit_if(self, node):
        after_label = f'_if{self.get_next_label_id()}'
        node.children[0].accept(self)
        self.bytecode.append(f'jz {after_label}')
        node.children[1].accept(self)
        self.bytecode.append(after_label + ':')

    def visit_while(self, node):
        condition_check_label = f'_while_condition{self.get_next_label_id()}'
        after_label = f'_while_after{self.get_next_label_id()}'

        self.bytecode.append(condition_check_label + ':')
        node.children[0].accept(self)
        self.bytecode.append(f'jz {after_label}')
        node.children[1].accept(self)
        self.bytecode.append(f'jump {condition_check_label}')
        self.bytecode.append(after_label + ':')

    def visit_continue(self, node):
        pass

    def visit_break(self, node):
        pass

    def visit_code_block(self, node):
        self.symbol_table = SymbolTable(self.symbol_table)
        node.symtable = self.symbol_table
        self.current_relative_address = 0
        self.current_memory_size = 0
        for child in node.children:
            child.accept(self)

    def visit_function_definition(self, node):
        pass

    def visit_function_call(self, node):
        pass

    def visit_return(self, node):
        pass
