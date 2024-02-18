from abc import ABC


class Parser(ABC):

    def parse(self, tokens):
        raise NotImplementedError
