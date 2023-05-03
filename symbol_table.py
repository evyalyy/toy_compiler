class Symbol:
    Id, Type, Function, Pointer = 0, 1, 2, 3

    def __init__(self, _name):
        self.name = _name
        self.symbol_type = None

    def __str__(self):
        raise NotImplementedError()


class SymbolId(Symbol):

    def __init__(self, _name, tp, address):
        super().__init__(_name)
        self.symbol_type = Symbol.Id
        self.type = tp
        self.address = address

    def __str__(self):
        return f'SymbolId: <{self.name}> of type <{self.type.name}> at {self.address}'


class SymbolType(Symbol):
    def __init__(self, _name, _size):
        super().__init__(_name)
        self.symbol_type = Symbol.Type
        self.size = _size

    def __str__(self):
        return f'SymbolType: <{self.name}> of size {self.size}'


class SymbolPointer(SymbolType):
    def __init__(self, base_type):
        super().__init__(base_type.name + '*', 1)
        self.symbol_type = Symbol.Pointer
        self.base_type = base_type

    def __str__(self):
        return f'SymbolPointer: to type <{self.base_type.name}>'


class SymbolFunction(Symbol):
    def __init__(self, _name, _ret_type, args):
        """
         args = [(type_symbol,name),(type_symbol,name)...]
         e.g. args = [SymbolType('int',1),'arg1',SymbolType('float',4),'arg2']
        """
        super().__init__(_name)
        self.symbol_type = Symbol.Function

        self.ret_type = _ret_type

        self.args = args
        self.label = 'func_%s' % _name

        self.args_size = 0
        if len(self.args) > 0:
            self.args_size = sum(map(lambda arg: arg[0].size, self.args))

    def __str__(self):
        args_str = ','.join(map(lambda arg: f'{arg[0].name} {arg[1]}', self.args))
        return f'SymbolFunction: {self.ret_type.name} {self.name}({args_str})'


class SymbolTable:

    def __init__(self, p=None):

        self.table = {}
        self.parent = p

    def find(self, name):

        curr_table = self
        while curr_table is not None:
            if name in curr_table.table:
                return curr_table.table[name]

            curr_table = curr_table.parent
        return None

    def add(self, sym):

        if sym.name not in self.table:
            self.table[sym.name] = sym
            return self.table[sym.name]
        else:
            raise KeyError('Symbol %s already present in current level table.' % sym.name)

    def show(self, prefix=''):

        out = ''
        for v in self.table.values():
            out += prefix + str(v) + '\n'

        if self.parent is None:
            return out

        out += prefix + 'Parent:\n'
        out += self.parent.show(prefix + ' ')

        return out


if __name__ == '__main__':
    def test():
        table = SymbolTable()
        table.add(SymbolType('int', 4))
        table.add(SymbolType('bool', 1))
        table.add(SymbolType('float', 1))

        itype = table.find('int')
        btype = table.find('bool')
        ftype = table.find('float')

        table.add(SymbolId('x', itype, 0))
        table.add(SymbolId('y', btype, 1))

        print(table.find('x'))
        print(table.find('y'))

        block = SymbolTable(table)

        block.add(SymbolId('x', ftype, 2))

        s = block.find('x')
        s.value = 100

        print(block.find('x'))

        args = [(itype, 'a1'), (ftype, 'a2')]

        table.add(SymbolFunction('foo', itype, args))

        print(block.show())
    test()
