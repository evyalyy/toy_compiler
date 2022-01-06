# -*- coding=utf-8 -*-

def remove_comments(code, comment_sym='//'):
    curr_idx = 0
    n = len(code)
    lines = code.split('\n')
    out_lines = []
    # print('Preprocessing')
    for line in lines:
        comment_start = line.find(comment_sym)
        # print('line:','"%s"' % line)
        # print('Found comment:',comment_start)
        if comment_start < 0:
            out_lines.append(line)
            continue
        line = line[:comment_start]
        # print('After comment removal:','"%s"' % line)
        out_lines.append(line)

    return '\n'.join(out_lines)


def parse(cmd):
    if cmd == '':
        return None, None
    parts = cmd.strip().split(' ')
    arg = None
    op = parts[0]
    if len(parts) > 1:
        arg = int(parts[1])

    return op, arg


def preprocess_code(code):
    code = remove_comments(code, '//')
    lines = code.split(';')
    lines = [s.strip() for s in lines]
    lines = [s for s in lines if len(s) > 0]

    # form map of labels and rows where each label is defined
    # allows to use integer indices for jumps
    labels = {}
    for i, line in enumerate(lines):
        parts = line.split(':')
        while len(parts) > 1:
            lab = parts.pop(0).strip()
            labels[lab] = i

    # replace labels in commands to numbers of corresponding lines
    for i, line in enumerate(lines):
        parts = line.split(':')
        for j in range(len(parts)):
            parts[j] = parts[j].strip()
        cmd = parts[-1]
        lines[i] = cmd
        cmd_parts = cmd.split(' ')
        jmp_target = cmd_parts[-1]
        if jmp_target in labels:
            lines[i] = cmd.replace(jmp_target, str(labels[jmp_target]))

    # parse all commands to command and argument
    for i, line in enumerate(lines):
        lines[i] = tuple(parse(line))

    return lines, labels


class StackFrame(object):

    def __init__(self, sp, ip, mem_start, mem_end=None):
        self.sp = sp
        self.ip = ip
        self.mem_start = mem_start
        self.mem_end = mem_end if mem_end is not None else mem_start

    def __str__(self):
        s = 'sp=%d; ip=%d; mem:[%d,%d]' % (self.sp, self.ip, self.mem_start, self.mem_end)
        return s


class VirtualMachine:

    def __init__(self):

        self.curr_mem_size = 0
        self.memory = [0] * self.curr_mem_size

        self.default_gmemory_size = 100
        self.gmemory = [] * self.default_gmemory_size

        self.MAX_STACK_SIZE = 1000
        self.stack = [0] * self.MAX_STACK_SIZE

        self.fstack = [StackFrame(-1, 0, 0, 0)]
        self.sframe = self.fstack[-1]

        self.ip = self.sframe.ip
        self.sp = self.sframe.sp
        self.ip_changed = False

        self.code = None

    def nop(self):
        pass

    def push(self, arg):
        self.sp += 1
        if self.sp >= len(self.stack):
            self.stack.extend([0] * len(self.stack))
        self.stack[self.sp] = arg

    def pop(self):
        # If current SP is equal to current frame SP
        # this means that stack is empty
        if self.sp <= self.sframe.sp:
            raise IndexError('Stack underflow in POP')
        self.sp -= 1

    def top(self):
        if self.sp <= self.sframe.sp:
            raise IndexError('Stack underflow in TOP')
        return self.stack[self.sp]

    def next(self):
        if self.sp <= self.sframe.sp + 1:
            raise IndexError('Stack underflow in NEXT')
        return self.stack[self.sp - 1]

    def putnext(self):
        self.push(self.next())

    def load(self, arg):

        arg += self.sframe.mem_start

        if arg < self.sframe.mem_start or arg >= self.sframe.mem_end:
            msg = 'Reading outside memory! '
            msg += 'Requested %d, but memory bounds are ' % arg
            msg += '[%d; %d]' % (self.sframe.mem_start, self.sframe.mem_end)
            raise IndexError(msg)

        self.push(self.memory[arg])

    def store(self, arg):

        arg += self.sframe.mem_start

        if self.sp <= self.sframe.sp:
            raise IndexError('Stack underflow in STORE')
        if arg < self.sframe.mem_start or arg >= self.sframe.mem_end:
            msg = 'Writing outside memory! '
            msg += 'Requested %d, but memory bounds are ' % arg
            msg += '[%d; %d]' % (self.sframe.mem_start, self.sframe.mem_end)
            raise IndexError(msg)

        self.memory[arg] = self.top()
        self.pop()

    def swap(self):
        v1, v2 = self.binary_op_extract_args_('SWAP')
        self.push(v2)
        self.push(v1)

    def dup(self):
        self.push(self.top())

    def binary_op_extract_args_(self, _name):
        if self.sp <= self.sframe.sp + 1:
            raise IndexError('%s requires at least 2 arguments on stack' % _name)
        v2 = self.top()
        self.pop()
        v1 = self.top()
        self.pop()
        return v1, v2

    def sub(self):
        v1, v2 = self.binary_op_extract_args_('SUB')
        res = v1 - v2
        self.push(res)

    def add(self):
        v1, v2 = self.binary_op_extract_args_('ADD')
        res = v1 + v2
        self.push(res)

    def mul(self):
        v1, v2 = self.binary_op_extract_args_('MUL')
        res = v1 * v2
        self.push(res)

    def div(self):
        v1, v2 = self.binary_op_extract_args_('DIV')
        res = v1 / v2
        self.push(res)

    def dec(self):
        self.push(1)
        self.sub()

    def inc(self):
        self.push(1)
        self.add()

    def lt(self):
        v1, v2 = self.binary_op_extract_args_('LT')
        res = int(v1 < v2)
        self.push(res)

    def gt(self):
        v1, v2 = self.binary_op_extract_args_('GT')
        res = int(v1 > v2)
        self.push(res)

    def eq(self):
        v1, v2 = self.binary_op_extract_args_('EQ')
        res = int(v1 == v2)
        self.push(res)

    def neq(self):
        v1, v2 = self.binary_op_extract_args_('NEQ')
        res = int(v1 != v2)
        self.push(res)

    def jump(self, arg):
        self.ip = arg
        self.ip_changed = True

    def jz(self, arg):
        val = self.top()
        self.pop()
        if 0 == val:
            self.jump(arg)

    def jnz(self, arg):
        val = self.top()
        self.pop()
        if 0 != val:
            self.jump(arg)

    def call(self, arg):
        # arguments for procedure are assumed to be on stack already
        # number of arguments is at the top of the stack

        args_size = self.top()
        self.pop()

        sf = StackFrame(self.sp - args_size, self.ip, self.sframe.mem_end)
        self.fstack.append(sf)
        self.sframe = self.fstack[-1]
        self.jump(arg)

    def ret(self):

        retval = self.top()
        sf = self.fstack.pop()

        self.sframe = self.fstack[-1]
        self.ip = sf.ip
        self.sp = sf.sp

        self.push(retval)
        self.jump(self.ip + 1)

    def alloc(self):
        v = self.top()
        # self.show_(True,True)
        self.pop()
        if v < 0:
            raise ValueError('Invalid argument to alloc:', v)
        self.sframe.mem_end += v
        n = len(self.memory)
        if n <= self.sframe.mem_end:
            self.memory += [0] * (self.sframe.mem_end - n)
        # self.memory += [0]*v
        # self.curr_mem_size = len(self.memory)

    def dealloc(self):
        v = self.top()
        self.pop()
        curr_msize = self.sframe.mem_end - self.sframe.mem_start
        if v > curr_msize:
            msg = 'Invalid argument to dealloc:'
            msg += ' requested %d but memory bounds are' % v
            msg += ' [%d;%d]' % (self.sframe.mem_start, self.sframe.mem_end)
            raise ValueError(msg)

        self.sframe.mem_end -= v
        # self.memory = self.memory[:self.curr_mem_size-v]
        # self.curr_mem_size = len(self.memory)

    def halt(self):
        self.is_stopped = True

    def execute(self, op, arg=None):

        op = op.lower()
        fn = getattr(self, op)
        if arg is not None:
            fn(arg)
        else:
            fn()

    def run_code(self, code):

        lines, labels = preprocess_code(code)
        print(lines)
        print(labels)
        ninstructions = len(lines)

        self.ip = 0
        self.sp = -1

        self.jump(labels['program'])

        self.ip_changed = False
        self.is_stopped = False

        while self.ip < ninstructions and not self.is_stopped:

            op, arg = lines[self.ip]

            self.execute(op, arg)
            if not self.ip_changed:
                self.ip += 1

            self.ip_changed = False

    def show(self, arg):

        if arg == 0:
            return

        if arg == 1:
            self.show_(True)

        if arg == 2:
            self.show_(True, True)

    def show_(self, show_stack=False, show_mem=False):
        if show_stack:
            s_start = self.sframe.sp
            s_end = self.sp
            local_sz = s_end - s_start

            fmt = 'Stack (sp=%d,sstart=%d,size=%d):\n'
            stack_str = fmt % (self.sp, s_start, local_sz)

            disp_stack = self.stack[s_start + 1:s_end + 1]

            stack_str += ' ' + str(disp_stack)
            print(stack_str)
            print('Full stack:', self.stack[:s_end + 1])

            print('Memory stack:')
            for f in self.fstack[::-1]:
                print('\t ', f)
        if show_mem:
            print('Memory (size=%d):\n' % (len(self.memory)), self.memory)
            ms = self.sframe.mem_start
            me = self.sframe.mem_end
            n = me - ms
            print('Local memory (size=%d):\n' % n, self.memory[ms:me])


if __name__ == '__main__':
    code = '''
    // Code for factorial
    fact:
        dup;
        push 2;
        lt;
        jz ok;        
    //less2:
        // Now 1 is on stack. Return it
        ret;
    ok:
    // Do multiplication
        dup;
        dec;
        push 1;
        call fact;
        mul;
        ret;

    program:
        push 15; // Put argument on stack
        push 1;
        // Fact procedure takes one argument <5>
        call fact;
        halt;
    '''

    # code = '''

    # test2:
    #     push 3;
    #     push 2;
    #     add;
    #     push 2;
    #     alloc;
    #     show 2;
    #     store 0;
    #     load 0;
    #     show 2;
    #     ret;

    # test:
    #     push 2;
    #     alloc;
    #     show 2;
    #     push 10;
    #     push 20;
    #     store 0;
    #     store 1;
    #     load 1;
    #     load 0;
    #     add;
    #     show 2;
    #     push 0;
    #     call test2;
    #     ret;

    # program:
    #     push 7;
    #     push 8;
    #     add;
    #     push 0;
    #     call test;
    #     halt;
    # '''

    vm = VirtualMachine()

    vm.run_code(code)

    print('After execution:')
    vm.show_(True, True)

    unused = '''
           PUSH 9;
    while:
          JZ end;
          dup;
          load 0;
          add;
          store 0;
          pop;
          dec;
          JUMP while;
    end:
        pop;  
        load 0;
        push 55;
        lt;
    '''

    # code = '''
    # program:

    #     push 10;
    #     push 20;
    #     add;
    #     jnz test;
    # cont:
    #     push 11;
    #     push 12;
    #     sub;
    #     jnz test0;
    #     push 1000;

    # test0:
    # test:
    #     push 30;

    #     halt;

    # '''
