from ast_visitor import AstVisitor


class PrintVisitor(AstVisitor):

    def __init__(self):
        self.level = 0

    @property
    def prefix_(self):
        return '  ' * self.level

    def visit_children_(self, node):
        self.level += 1
        for ch in node.children:
            ch.accept(self)
        self.level -= 1

    def visit_id(self, node):
        print(self.prefix_, f'Id({node.name})')
        pass

    def visit_num(self, node):
        print(self.prefix_, f'Number({node.value})')

    def visit_expr(self, node):
        print(self.prefix_, f'Expression({node.op}):{{')
        self.visit_children_(node)
        print(self.prefix_, '}')

    def visit_entry_point(self, node):
        print(self.prefix_, 'EntryPoint()')
        pass

    def visit_declaration(self, node):
        msg = f'Declaration(`{node.name.name}` of type `{node.tp.name}`)'
        if node.children:
            msg += ' assigned:'
        print(self.prefix_, msg)
        if node.children:
            self.visit_children_(node)

    def visit_if_or_while(self, node):
        self.level += 1
        node.children[0].accept(self)
        self.level -= 1
        print(self.prefix_, ') {')
        self.level += 1
        node.children[1].accept(self)
        self.level -= 1
        print(self.prefix_, '}')

    def visit_if(self, node):
        print(self.prefix_, 'If (')
        self.visit_if_or_while(node)

    def visit_while(self, node):
        print(self.prefix_, 'while (')
        self.visit_if_or_while(node)

    def visit_continue(self, node):
        print(self.prefix_, 'continue')

    def visit_break(self, node):
        print(self.prefix_, 'break')

    def visit_code_block(self, node):
        print(self.prefix_, 'CodeBlock {')
        self.visit_children_(node)
        print(self.prefix_, '}')

    def visit_function_definition(self, node):
        args = ','.join(f'{arg[1].name} of type {arg[0].name}' for arg in node.args)
        print(self.prefix_, f'Function {node.func_name.name}({args}) -> {node.ret_type.name} {{')
        self.visit_children_(node)
        print(self.prefix_, '}')

    def visit_function_call(self, node):
        print(self.prefix_, f'call {node.func_name} with args: (')
        self.visit_children_(node)
        print(self.prefix_, ')')

    def visit_return(self, node):
        print(self.prefix_, f'return (')
        self.visit_children_(node)
        print(self.prefix_, ')')
