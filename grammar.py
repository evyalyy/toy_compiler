def is_uppercase(s):
    return s == s.upper()


class Grammar(dict):

    def __init__(self):
        dict.__init__(self)

    def all_symbols(self):
        out = set()
        for prod_list in list(self.values()):
            for prod in prod_list:
                tmp = set(prod)
                out.update(tmp)

        out.update(set(self.keys()))
        return out

    def add_prod(self, nterminal, prod):
        if nterminal in list(self.keys()):
            self[nterminal].append(prod)
        else:
            self[nterminal] = [prod]

    def add_prod_str(self, inp):
        parts = inp.split('->')
        if len(parts) != 2:
            raise ValueError('Wrong input:%s' % inp)

        nterminal = parts[0].strip()
        prod = parts[1].strip().split(' ')
        self.add_prod(nterminal, prod)

    def is_nonterminal(self, s):
        return is_uppercase(s) and s.isalpha()

    def non_terminals(self):
        return list(filter(self.is_nonterminal, self.all_symbols()))

    def terminals(self):
        return [s for s in self.all_symbols() if not self.is_nonterminal(s)]

    # def first(self,s):

    #     out = set()
    #     for sym in s:
    #         if self.is_nonterminal(sym):
    #             for prod in self[sym]:
    #                 out |= self.first(prod)
    #             break

    #         out.add(sym)
    #         break

    #     return out


if __name__ == '__main__':
    gr = Grammar()
    gr.add_prod_str('EXPR -> TERM + EXPR')
    gr.add_prod_str('EXPR -> TERM - EXPR')
    gr.add_prod_str('EXPR -> TERM')
    gr.add_prod_str('TERM -> id')

    print(gr)
