import os
import mel_parser


def main():
    prog = mel_parser.parse('''
        input a input b  /* comment 1
        input c
        */
        c = a + b * (2 - 1) + 0  // comment 2
        output c + pow(5, 2+0, true)

        if (a + 7) b = 9
    ''')
    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
