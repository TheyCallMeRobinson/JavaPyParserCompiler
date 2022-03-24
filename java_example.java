class OldClass {
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
pyparsing, larc, pypeg

public class Main {
    public static void main(String[] args) {
        OldClass.oldClassMethod(10, 20.5);
    }
}
