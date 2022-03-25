import os
import mel_parser


def main():
    prog = mel_parser.parse('''
        c = a + b * (2 - 1) + 0  // comment 2

        if (a+7) b = 9
        while (a + 10) {a = 10}
        for (d; a+10; c) {b = 50}
    ''')
    print(*prog.tree, sep=os.linesep)


if __name__ == "__main__":
    main()
