from contextlib import suppress
import inspect

import pyparsing as pp
from pyparsing import pyparsing_common as ppc

from mel_ast import *


def _make_parser():
    LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
    LBRACK, RBRACK = pp.Literal("[").suppress(), pp.Literal("]").suppress()
    LBRACE, RBRACE = pp.Literal("{").suppress(), pp.Literal("}").suppress()
    SEMI, COMMA = pp.Literal(';').suppress(), pp.Literal(',').suppress()
    ASSIGN = pp.Literal('=')
    MULT, ADD = pp.oneOf('* /'), pp.oneOf('+ -')

    IF, ELSE = pp.Keyword('if').suppress(), pp.Keyword('else').suppress()
    FOR, WHILE = pp.Keyword('for').suppress(), pp.Keyword('while').suppress()
    TRUE, FALSE = pp.Keyword('true'), pp.Keyword('false')
    INT, DOUBLE, CHAR, FLOAT = pp.Keyword('int').suppress(), pp.Keyword('double').suppress(), \
                               pp.Keyword('char').suppress(), pp.Keyword('float').suppress()
    STRING, OBJECT = pp.Keyword('String').suppress(), pp.Keyword('Object').suppress()
    INTARR, STRINGARR = pp.Keyword('int[]').suppress(), pp.Keyword('String[]').suppress()
    CLASS = pp.Keyword('class').suppress()
    STATIC = pp.Keyword('static').suppress()
    PUBLIC, PRIVATE = pp.Keyword('public').suppress(), pp.Keyword('private').suppress()
    NEW = pp.Keyword('new').suppress()
    RETURN = pp.Keyword('return').suppress()

    keywords = IF | \
               ELSE | \
               WHILE | \
               FOR | \
               TRUE | \
               STRING | \
               OBJECT | \
               INTARR | \
               STRINGARR | \
               CLASS | \
               STATIC | \
               PUBLIC | \
               PRIVATE | \
               NEW | \
               RETURN

    num = pp.Regex('[+-]?\\d+\\.?\\d*([eE][+-]?\\d+)?')
    str_ = pp.QuotedString('"', escChar='\\', unquoteResults=False, convertWhitespaceEscapes=False)
    literal = num | str_ | TRUE | FALSE
    # single_literal = LPAR | RPAR | LBRACK | RBRACK | LBRACE | RBRACE | SEMI | COMMA | \
    #     ASSIGN | MULT | ADD
    ident = (~keywords + ppc.identifier.copy()).setName('ident')

    expr = pp.Forward()

    func_call = ident + LPAR + pp.Optional(expr + pp.ZeroOrMore(COMMA + expr)) + RPAR
    group = (
            literal |
            func_call |  # обязательно перед ident, т.к. приоритетный выбор (или использовать оператор ^ вместо | )
            ident |
            LPAR + expr + RPAR
    )
    mult = group + pp.ZeroOrMore(MULT + group)
    add = mult + pp.ZeroOrMore(ADD + mult)

    expr << add

    stmt_wout_semi = pp.Forward()
    stmt_with_semi = pp.Forward()

    assign = ident + ASSIGN.suppress() + add

    if_ = IF + LPAR + expr + RPAR + stmt_wout_semi + \
          pp.Optional(ELSE + stmt_wout_semi)
    for_ = FOR + LPAR + expr + SEMI + expr + SEMI + expr + RPAR + LBRACE + stmt_wout_semi + RBRACE
    while_ = WHILE + LPAR + expr + RPAR + LBRACE + stmt_wout_semi + RBRACE
    stmt_wout_semi << (
            if_ |
            for_ |
            while_
    )
    stmt_with_semi << (
        assign
    )
    stmt_list = pp.ZeroOrMore(stmt_wout_semi)
    program = stmt_list.ignore(pp.cStyleComment).ignore(pp.dblSlashComment) + pp.StringEnd()

    start = program

    def set_parse_action_magic(rule_name: str, parser_element: pp.ParserElement) -> None:
        if rule_name == rule_name.upper():
            return
        # if getattr(parser_element, 'name', None) and parser_element.name.isidentifier():
        #    rule_name = parser_element.name
        if rule_name in ('mult', 'add'):
            def bin_op_parse_action(s, loc, tocs):
                node = tocs[0]
                for i in range(1, len(tocs) - 1, 2):
                    node = BinOpNode(BinOp(tocs[i]), node, tocs[i + 1])
                return node

            parser_element.setParseAction(bin_op_parse_action)
        else:
            cls = ''.join(x.capitalize() for x in rule_name.split('_')) + 'Node'
            with suppress(NameError):
                cls = eval(cls)
                if not inspect.isabstract(cls):
                    def parse_action(s, loc, tocs):
                        return cls(*tocs)

                    parser_element.setParseAction(parse_action)

    for var_name, value in locals().copy().items():
        if isinstance(value, pp.ParserElement):
            set_parse_action_magic(var_name, value)

    return start


parser = _make_parser()


def parse(prog: str) -> StmtListNode:
    return parser.parseString(str(prog))[0]
