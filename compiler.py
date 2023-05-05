from my_lexer import Lexer
from my_parser import Parser, print_ast
from virtual_machine import VirtualMachine

if __name__ == '__main__':
    code = '''
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

    lex = Lexer()
    tokens = lex.analyze(code)

    print('Parsing')
    pr = Parser(tokens)
    ast = pr.program()

    print_ast(ast)

    cmd_list = ast.emit()

    code = ';\n'.join(cmd_list) + ';\nhalt;'
    code = code.replace(':;', ':')
    print(code)

    vm = VirtualMachine()
    vm.run_code(code)
    vm.show(2)
