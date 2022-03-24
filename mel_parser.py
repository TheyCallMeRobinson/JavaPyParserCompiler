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
    
    INPUT = pp.Keyword('input')
    OUTPUT = pp.Keyword('output')
    IF, ELSE = pp.Keyword('if').suppress(), pp.Keyword('else').suppress()
    FOR, WHILE = pp.Keyword('for').suppress(), pp.Keyword('while').suppress()
    TRUE, FALSE = pp.Keyword('true'), pp.Keyword('false')
    INT = pp.Keyword('int').suppress()
    
    keywords = INPUT | \
               OUTPUT | \
               IF | \
               ELSE | \
               WHILE | \
               FOR | \
               TRUE | \
               INT
    
    num = pp.Regex('[+-]?\\d+\\.?\\d*([eE][+-]?\\d+)?')
    str_ = pp.QuotedString('"', escChar='\\', unquoteResults=False, convertWhitespaceEscapes=False)
    literal = num | str_ | TRUE | FALSE
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

    stmt = pp.Forward()

    input = INPUT.suppress() + ident
    output = OUTPUT.suppress() + add
    assign = ident + ASSIGN.suppress() + add

    if_ = IF + LPAR + expr + RPAR + stmt + \
        pp.Optional(ELSE + stmt)
    for_ = FOR + LPAR + expr + SEMI + expr + SEMI + expr + RPAR + LBRACE + stmt + RBRACE
    while_ = WHILE + LPAR + expr + RPAR + LBRACE + stmt + RBRACE
    stmt << (
        input |
        output |
        assign |
        if_ |
        for_ |
        while_
    )
    stmt_list = pp.ZeroOrMore(stmt)
    program = stmt_list.ignore(pp.cStyleComment).ignore(pp.dblSlashComment) + pp.StringEnd()

    start = program

    def set_parse_action_magic(rule_name: str, parser_element: pp.ParserElement) -> None:
        if rule_name == rule_name.upper():
            return
        #if getattr(parser_element, 'name', None) and parser_element.name.isidentifier():
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
