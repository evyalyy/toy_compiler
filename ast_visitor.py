from abc import ABC, abstractmethod


class AstVisitor(ABC):

    @abstractmethod
    def visit_id(self, node):
        pass

    @abstractmethod
    def visit_num(self, node):
        pass

    @abstractmethod
    def visit_expr(self, node):
        pass

    @abstractmethod
    def visit_entry_point(self, node):
        pass

    @abstractmethod
    def visit_declaration(self, node):
        pass

    @abstractmethod
    def visit_if(self, node):
        pass

    @abstractmethod
    def visit_while(self, node):
        pass

    @abstractmethod
    def visit_continue(self, node):
        pass

    @abstractmethod
    def visit_break(self, node):
        pass

    @abstractmethod
    def visit_code_block(self, node):
        pass

    @abstractmethod
    def visit_function_definition(self, node):
        pass

    @abstractmethod
    def visit_function_call(self, node):
        pass

    @abstractmethod
    def visit_return(self, node):
        pass
