from ast_visitor import AstVisitor


class ASTNode:

    def __init__(self, parent=None):
        self.parent = parent
        self.children = []

    def add_child(self, node):
        node.parent = self
        self.children.append(node)

    def accept(self, v: AstVisitor):
        raise NotImplementedError()

    def emit(self):
        raise NotImplementedError()
