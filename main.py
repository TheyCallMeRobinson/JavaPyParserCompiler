import os

from compiler_demo import my_parser

def main() -> None:
    test1 = '''private class A{
    {
    b();
    int a = 1+2+b().a.b();
    a = 1;
    }
    int a(int b){
        int a = a().b.c().c.v();
        int a = a();
        a();
    }
    public class A{
    class A{
    int a = 0, b = a, c;
    String a = 0, b = a, c;
    }
    }
    }
    }'''
    test2 = '''class OldClass {
    public static int oldClassMethod(int a, double b) {
        NewClass nc1 = new NewClass(a, b);
        NewClass nc2 = new NewClass(0, 0.0);
        int result = nc1.classMethod(50);
        return result;
    }
}

class NewClass {
    private int privateInt;
    public Double publicDouble;

    public NewClass(int i, Double d) {
        privateInt = i;
        publicDouble = d;
    }

    public int classMethod(int u) {
        int a1 = 5, a2 = 10;
        int varInt = 2;
        double varDouble = 2.0;
        String varString = "hello";
        Object varNull = null;
        int[] array = new int[]{1, 2, 3};
        double sum = array[0] + array[1];
        double dif = a1 - a2;
        double multiply = a1 * a2;
        //double power = Math.pow(a1, a2);
        double division = a1 / a2;
        if (a1 > 1) {
            for (int i = 0; a2 <= 10; i++) {
                break;
            }
        } else {
            //System.out.print("Hello, World!");
        }
        int a = 2;
        while (a-- > 0) {
            int c = 5;
            do {
                c++;
            } while (c > 0);
        }
        return a;
    }
}
public class Main {
    public static void main(String[] args) {
        OldClass.oldClassMethod(10, 20.5);
    }
}'''
    test3 = '''class NewClass {
        public int classMethod(int u) {
            int a1 = 5, a2 = 10;
            int varInt = 2;
            double varDouble = 2.0;
            String varString = "hello";
            Object varNull = null;
            double dif = a1 - a2;
            double multiply = a1 * a2;
            double division = a1 / a2;
            if (a1 > 1) {
            } else {
            }
            for (;;) {
                }
            int a = 2;
            return a;
        }
    }
        public class Main {
        public static void main(String[] args) {
            OldClass.oldClassMethod(10, 20.5);
        }
'''
    test4 = '''
    public class Main {
        int a = 1;
    }'''
    prog = my_parser.parse(test4)
    ast_tree = prog.tree

    print(*ast_tree, sep=os.linesep)


if __name__ == "__main__":
    main()
