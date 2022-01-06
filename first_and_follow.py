import re

GRAMMAR_PATH = './grammar_description.txt'
EPSILON = "e"

desc = [line.strip() for line in open(GRAMMAR_PATH,'r')]
desc = [line for line in desc if len(line) > 0 and not line.startswith('#')]

def is_epsilon(s):
    return s == EPSILON

def is_terminal(s):
    return s.startswith("'") and not is_epsilon(s)


def is_nonterminal(s):
    return not is_terminal(s) and not is_epsilon(s)


def sts(s):
    out = '{' + ','.join(s) + '}'
    return out

def lts(s):
    return '[' + ','.join(s) + ']'

def parse_description(desc,verbose=False):
    grammar = {}

    curr_prod_idx = 0
    line_idx = 1
    prod_list = [desc[0]]
    while line_idx < len(desc):
        if desc[line_idx].startswith('|'):
            prod_list[-1] = prod_list[-1]+desc[line_idx]
        else:
            prod_list.append(desc[line_idx])
        line_idx+=1
    for prod in prod_list:
        idx = prod.find('=')
        nonterminal = prod[:idx].strip()
        rest = prod[idx+1:].strip()
        if verbose:
            print(nonterminal,' -> ',rest)

        rules = rest.split('|')
        if verbose:
            print('\t', rules)
        for rule in rules:
            symbols = [s.strip() for s in rule.split(',')]
            if verbose:
                print('\t\t',lts(symbols))
            if not nonterminal in grammar:
                grammar[nonterminal] = []
            grammar[nonterminal].append(symbols)

    return grammar



S = desc[0].split('=')[0].strip()
grammar = parse_description(desc)

max_nterm_name_len = max(list(map(len,list(grammar.keys()))))


# for k,v in list(grammar.items()):
#     print(k)
#     for rule in v:
#         print(lts(rule),':',list(map(is_terminal,rule)))


def First(symbols):
    global grammar

    if isinstance(symbols,str):
        symbols = [symbols]

    # print 'In first at', symbols
    first = set()
    if len(symbols) == 1 :
        # print 'Single symbol'
        X = symbols[0]
        if is_terminal(X):
            return set([X])
        if is_epsilon(X):
            # raise ValueError('WTF on X = '+X)
            return set([X])

        for rule in grammar[X]:
            # print 'Processing rule',rule
            if len(rule) == 1 and is_epsilon(rule[0]):
                first.add(EPSILON)
            else:
                first.update(First(rule))
        return first
    else:
        # print 'Multiple symbols'
        y1 = symbols[0]
        # print 'Leading symbol:',y1
        leading_first = First([y1])
        # print 'Leading first:',leading_first
        if EPSILON not in leading_first:
            first = leading_first
            return first
        else:
            leading_first.remove(EPSILON)
            rest_first = First(symbols[1:])

            first = leading_first | rest_first

            if all([EPSILON in First(s) for s in symbols[1:]]):
                first.add(EPSILON)
            return first


follow = {}
for k in list(grammar.keys()):
    follow[k] = None

# print('Start symbol:',S)
follow[S] = set(['$'])

def Follow(grammar,follow,nonterminal,verbose=False):

    rules = []
    for k,prod_list in list(grammar.items()):

        for prod in prod_list:
            if nonterminal in prod:
                rules.append((k,prod))

    if verbose:
        print('Computing for', nonterminal)
        print('List of productions:')
        for r in rules:
            print('\t',r[0],'->',lts(r[1]))

    if follow[nonterminal] is None:
        follow[nonterminal] = set()

    for k,prod in rules:

        idx = prod.index(nonterminal)
        if idx == len(prod) - 1:
            if follow[k] is None:
                Follow(grammar,follow,k,verbose)
            follow[nonterminal].update(follow[k])
        else:
            first = First(prod[idx+1:])
            if EPSILON in first:
                if verbose:
                    print('Epsilon in suffix')
                if follow[k] is None:
                    Follow(grammar,follow,k)
                follow[nonterminal].update(follow[k])
            resid = first - set([EPSILON])
            if verbose:
                print('To be added (rule: %s -> %s: %s) RESID:' % (k,lts(prod),sts(first)),sts(resid))
            follow[nonterminal].update(resid)
    if verbose:
        print('Result:',sts(follow[nonterminal]))


def has_epsilon_production(nonterminal):
    global grammar

    for prod in grammar[nonterminal]:
        if len(prod) == 1 and is_epsilon(prod[0]):
            return True
    return False


def can_produce_epsilon(nonterminal):
    global grammar 

    if has_epsilon_production(nonterminal):
        return True

    for prod in grammar[nonterminal]:

        if any(map(is_terminal,prod)):
            continue

        if all([can_produce_epsilon(s) for s in prod if s != nonterminal]):
            return True
        # for sym in prod:
        #     if sym == nonterminal:
        #         continue

        #     if not can_produce_epsilon(sym):
        #         break

    return False


def can_string_produce_epsilon(symbols):

    global grammar

    if len(symbols) == 1 and is_epsilon(symbols[0]):
        return True

    if any(map(is_terminal,symbols)):
        return False   

    return all(map(can_produce_epsilon,symbols))


dfs_marks = {}
for nterm in grammar:
    dfs_marks[nterm] = 0

def DFS_FOLLOW(nonterminal,verbose=False):
    global grammar,follow

    dfs_marks[nonterminal] = 1

    Follow(grammar,follow,nonterminal,verbose)

    for prod in grammar[nonterminal]:
        for sym in prod:
            if not is_nonterminal(sym):
                continue
            # print sym
            if dfs_marks[sym] != 0:
                continue

            DFS_FOLLOW(sym,verbose)


DFS_FOLLOW(S)

first = {}
for nterm in grammar:
    first[nterm] = First(nterm)

sorted_nterms = sorted(grammar.keys())

for nterm in sorted_nterms:
    print('FOLLOW(%s) is:'%nterm.ljust(max_nterm_name_len),sts(follow[nterm]))

for nterm in sorted_nterms:
    print('FIRST(%s) is:'%nterm.ljust(max_nterm_name_len),sts(first[nterm]))

for nterm in sorted_nterms:
    print('Can \"%s\" produce epsilon:' % nterm.ljust(max_nterm_name_len),can_produce_epsilon(nterm))


# LL(1) criterion check
is_LL1 = True
for nterm,prod_list in list(grammar.items()):

    fs = list(map(First,prod_list))
    nprods = len(prod_list)
    for i in range(nprods):
        alpha = prod_list[i]
        for j in range(nprods):
            if j == i:
                continue
            beta = prod_list[j]

            intersection = fs[i] & fs[j]
            if len(intersection) > 0:
                is_LL1 = False
                print('GRAMMAR IS NOT LL(1)!!!!1 FIRST sets intersection')
                print(nterm)
                print('\t',lts(alpha),lts(beta))
                print('\t',sts(fs[i]),sts(fs[j]))

            if can_string_produce_epsilon(alpha):
                if len(fs[j] & follow[nterm]) > 0:
                    is_LL1 = False
                    print('GRAMMAR IS NOT LL(1)!!!!1 FIRST-FOLLOW intersection')
                    print(nterm)
                    print('\t',lts(alpha),lts(beta))
                    print('\t',sts(fs[i]),sts(fs[j]))
                    print('FOLLOW(%s):' % nterm, sts(follow[nterm]))

if is_LL1:
    print('SUCCESS!!! GRAMMAR IS LL(1)')
