from my_lexer import Lexer
from parser import Parser
from my_parser import OldParser
from virtual_machine import VirtualMachine


class Compiler:

    def __init__(self, parser: Parser, debug=False):
        self.parser = parser
        self.debug = debug

    def compile(self, code):
        lex = Lexer()
        tokens = lex.analyze(code)

        ast = self.parser.parse(tokens)

        cmd_list = ast.emit()

        code = ';\n'.join(cmd_list) + ';\nhalt;'
        code = code.replace(':;', ':')
        return code


if __name__ == '__main__':
    fibonacci_src = '''
    {
       func int foo(int x){
            var int tmp = 0;
            var int y = 10;
            tmp = x + y;
            if(tmp < 50){
                tmp = foo(tmp);
            }
            return tmp;
       }
       
       func int sum(int x, int y)
       {
         return x + y;
       }
       entry
       foo(1);
       //func int bar(){
       // var float x = 0;
       //}
        // var int n = 9;
        // var int prev1 = 1;
        // var int prev2 = 1;
        // while(n > 2){
        //     var int tmp = prev1;
        //     prev1 = prev1 + prev2;
        //     prev2 = tmp;
        //     n = n - 1;
        // }

       // var int n = 5;
       // var int result = 1;
       // while(n > 0){
       //      result = result * n;
       //      n = n - 1;
       // }
    }
    '''

    compiler = Compiler(OldParser(), debug=True)
    bytecode = compiler.compile(fibonacci_src)

    vm = VirtualMachine()
    vm.run_code(bytecode)
    vm.show(2)
