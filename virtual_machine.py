# -*- coding=utf-8 -*-

from preprocessing import remove_comments


def parse(cmd):
    if cmd == '':
        return None, None
    parts = cmd.strip().split(' ')
    arg = None
    op = parts[0]
    if len(parts) > 1:
        arg = int(parts[1])

    return op, arg


def preprocess_code(program_code):
    program_code = remove_comments(program_code, '//')
    lines = program_code.split(';')
    lines = [s.strip() for s in lines if len(s.strip()) > 0]

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
        parts = [p.strip() for p in line.split(':')]
        cmd = parts[-1]
        lines[i] = cmd
        cmd_parts = cmd.split(' ')
        jmp_target = cmd_parts[-1]
        if jmp_target in labels:
            lines[i] = cmd.replace(jmp_target, str(labels[jmp_target]))

    return [parse(line) for line in lines], labels


class StackFrame(object):

    def __init__(self, sp, ip, mem_start, mem_end=None):
        self.sp = sp
        self.ip = ip
        self.mem_start = mem_start
        self.mem_end = mem_end if mem_end is not None else mem_start

    def __str__(self):
        return f'sp={self.sp}; ip={self.ip}; mem:[{self.mem_start},{self.mem_end}]'


class VirtualMachine:

    def __init__(self, debug=False):

        self.curr_mem_size = 0
        self.memory = [0] * self.curr_mem_size

        self.INITIAL_STACK_SIZE = 1000
        self.stack = [0] * self.INITIAL_STACK_SIZE

        self.call_stack = [StackFrame(-1, 0, 0, 0)]
        self.frame = self.call_stack[-1]

        self.ip = self.frame.ip
        self.sp = self.frame.sp
        self.ip_changed = False
        self.is_stopped = False

        self.debug = debug

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
        if self.sp <= self.frame.sp:
            raise IndexError('Stack underflow in POP')
        self.sp -= 1

    def top(self):
        if self.sp <= self.frame.sp:
            raise IndexError('Stack underflow in TOP')
        return self.stack[self.sp]

    def next(self):
        if self.sp <= self.frame.sp + 1:
            raise IndexError('Stack underflow in NEXT')
        return self.stack[self.sp - 1]

    def load(self, arg):

        arg += self.frame.mem_start

        if arg < self.frame.mem_start or arg >= self.frame.mem_end:
            msg = 'Reading outside memory! '
            msg += 'Requested %d, but memory bounds are ' % arg
            msg += '[%d; %d]' % (self.frame.mem_start, self.frame.mem_end)
            raise IndexError(msg)

        self.push(self.memory[arg])

    def store(self, arg):

        arg += self.frame.mem_start

        if arg < self.frame.mem_start or arg >= self.frame.mem_end:
            msg = 'Writing outside memory! '
            msg += 'Requested %d, but memory bounds are ' % arg
            msg += '[%d; %d]' % (self.frame.mem_start, self.frame.mem_end)
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
        if self.sp <= self.frame.sp + 1:
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

        sf = StackFrame(self.sp - args_size, self.ip, self.frame.mem_end)
        self.call_stack.append(sf)
        self.frame = self.call_stack[-1]
        self.jump(arg)

    def ret(self):

        return_value = self.top()
        sf = self.call_stack.pop()

        self.frame = self.call_stack[-1]
        self.ip = sf.ip
        self.sp = sf.sp

        self.push(return_value)
        self.jump(self.ip + 1)

    def alloc(self):
        v = self.top()
        self.pop()
        if v < 0:
            raise ValueError('Invalid argument to alloc:', v)
        self.frame.mem_end += v
        n = len(self.memory)
        if n <= self.frame.mem_end:
            self.memory += [0] * (self.frame.mem_end - n)

    def dealloc(self):
        v = self.top()
        self.pop()
        curr_memory_size = self.frame.mem_end - self.frame.mem_start
        if v > curr_memory_size:
            msg = 'Invalid argument to dealloc:'
            msg += ' requested %d but memory bounds are' % v
            msg += ' [%d;%d]' % (self.frame.mem_start, self.frame.mem_end)
            raise ValueError(msg)

        self.frame.mem_end -= v

    def print(self):
        v = self.top()
        self.pop()
        print(v)

    def halt(self):
        self.is_stopped = True

    def execute(self, op, arg=None):

        op = op.lower()
        fn = getattr(self, op)
        if arg is not None:
            fn(arg)
        else:
            fn()

    def run_code(self, program_code):

        lines, labels = preprocess_code(program_code)
        if self.debug:
            print(lines)
            print(labels)
        num_instructions = len(lines)

        self.ip = 0
        self.sp = -1

        self.jump(labels['program'])

        self.ip_changed = False
        self.is_stopped = False

        while self.ip < num_instructions and not self.is_stopped:

            op, arg = lines[self.ip]
            if self.debug:
                arg_str = f'({arg})' if arg is not None else ''
                print(f'Execute {op.upper()}' + arg_str)

            self.execute(op, arg)
            if not self.ip_changed:
                self.ip += 1

            self.ip_changed = False

    def show(self, arg):

        if arg == 0:
            return

        if arg == 1:
            self._show_stack()

        if arg == 2:
            self._show_stack()
            self._show_memory()

    def _show_stack(self):
        s_start = self.frame.sp
        s_end = self.sp
        local_sz = s_end - s_start

        stack_str = f'Stack (sp={self.sp}, s_start={s_start}, size={local_sz}):\n'

        stack_to_show = self.stack[s_start + 1:s_end + 1]

        stack_str += ' ' + str(stack_to_show)
        print(stack_str)
        print('Full stack:', self.stack[:s_end + 1])

        print('Memory stack:')
        for f in self.call_stack[::-1]:
            print('\t ', f)

    def _show_memory(self):
        print(f'Memory (size={len(self.memory)}): {self.memory}\n')
        ms = self.frame.mem_start
        me = self.frame.mem_end
        n = me - ms
        print(f'Local memory (size={n}): {self.memory[ms:me]}\n')


if __name__ == '__main__':
    def read(file_path):
        with open(file_path, 'r') as f:
            return f.read()

    code = read('./virtual_machine_test_data/factorial.bytecode')

    vm = VirtualMachine(debug=False)

    vm.run_code(code)

    # print('After execution:')
    # vm.show(2)
