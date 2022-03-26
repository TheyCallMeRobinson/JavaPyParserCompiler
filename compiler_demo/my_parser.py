import inspect

import pyparsing as pp
from pyparsing import pyparsing_common as ppc

from .ast import *


# noinspection PyPep8Naming
def make_parser():
    LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
    LBRACK, RBRACK = pp.Literal("[").suppress(), pp.Literal("]").suppress()
    LBRACE, RBRACE = pp.Literal("{").suppress(), pp.Literal("}").suppress()
    SEMI, COMMA = pp.Literal(';').suppress(), pp.Literal(',').suppress()
    DOT = pp.Literal('.')
    ASSIGN = pp.Literal('=')

    ADD, SUB = pp.Literal('+'), pp.Literal('-')
    MUL, DIV, MOD = pp.Literal('*'), pp.Literal('/'), pp.Literal('%')
    AND = pp.Literal('&&')
    OR = pp.Literal('||')
    GE, LE, GT, LT = pp.Literal('>='), pp.Literal('<='), pp.Literal('>'), pp.Literal('<')
    NEQUALS, EQUALS = pp.Literal('!='), pp.Literal('==')
    P_EQ, M_EQ, DEL_EQ, MUL_EQ = pp.Literal('+='), pp.Literal('-='), pp.Literal('/='), pp.Literal('*=')

    PRIVATE = pp.Literal('private')
    PROTECTED = pp.Literal('protected')
    PUBLIC = pp.Literal('public')
    access_keys = PUBLIC | PROTECTED | PRIVATE

    # access = pp.Optional(PRIVATE | PROTECTED | PUBLIC)

    STATIC = pp.Literal('static')
    VOID = pp.Literal('void').suppress()

    CLASS = pp.Literal('class').suppress()

    IF = pp.Keyword('if')
    FOR = pp.Keyword('for')
    RETURN = pp.Keyword('return')
    NEW = pp.Keyword('new')
    keywords = IF | FOR | RETURN

    num = pp.Regex('[+-]?\\d+\\.?\\d*([eE][+-]?\\d+)?')
    str_ = pp.QuotedString('"', escChar='\\', unquoteResults=False, convertWhitespaceEscapes=False)
    literal = num | str_ | pp.Regex('true|false')

    ident = (~keywords + ppc.identifier.copy()).setName('ident')
    type_ = ident.copy().setName('type')+pp.Optional(LBRACK+RBRACK)
    access = ident.copy().setName('access')

    add = pp.Forward()
    expr = pp.Forward()
    stmt = pp.Forward()
    stmt_list = pp.Forward()
    body = pp.Forward()
    class_init = pp.Forward()
    func_stmt = pp.Forward()
    func_class_init = pp.Forward()
    func_body = pp.Forward()
    assign = pp.Forward()
    dot = pp.Forward()
    caller = pp.Forward()
    new = pp.Forward()

    call = ident + LPAR + pp.Optional(caller + pp.ZeroOrMore(COMMA + caller)) + RPAR
    new = NEW.suppress() + call

    assign = ident + ASSIGN.suppress() + caller
    var_inner = assign | ident
    vars_ = type_ + var_inner + pp.ZeroOrMore(COMMA + var_inner)

    group = (
            literal |
            dot |
            LPAR + caller + RPAR
    )

    dot << pp.Group((new | call | ident) + pp.ZeroOrMore(DOT + (new | call | ident))).setName(
        'bin_op')  # обязательно call перед ident, т.к. приоритетный выбор (или использовать оператор ^ вместо | )
    mult = pp.Group(group + pp.ZeroOrMore((MUL | DIV | MOD) + group)).setName('bin_op')
    add << pp.Group(mult + pp.ZeroOrMore((ADD | SUB) + mult)).setName('bin_op')
    compare1 = pp.Group(add + pp.Optional((GE | LE | GT | LT) + add)).setName('bin_op')
    compare2 = pp.Group(compare1 + pp.Optional((EQUALS | NEQUALS) + compare1)).setName('bin_op')
    logical_and = pp.Group(compare2 + pp.ZeroOrMore(AND + compare2)).setName('bin_op')
    logical_or = pp.Group(logical_and + pp.ZeroOrMore(OR + logical_and)).setName('bin_op')
    op_assign = pp.Group(logical_or + pp.ZeroOrMore((MUL_EQ | DEL_EQ | P_EQ | M_EQ) + logical_or)).setName('bin_op')
    expr << op_assign

    caller << expr
    param = type_ + ident
    params = pp.Optional(param + pp.ZeroOrMore(COMMA + param))
    func_struct = (access_keys | pp.Group(pp.Empty())) + (
            STATIC | pp.Group(pp.Empty())) + type_ + ident + LPAR + params + RPAR

    func = func_struct + func_body
    return_ = RETURN.suppress() + expr
    if_ = IF.suppress() + LPAR + expr + RPAR + func_body + \
          pp.ZeroOrMore(pp.Keyword("else if").suppress() + func_body) + \
          pp.Optional(pp.Keyword("else").suppress() + func_body)
    simple_stmt = new | assign | call | expr
    for_stmt_list0 = (pp.Optional(simple_stmt + pp.ZeroOrMore(COMMA + simple_stmt))).setName('stmt_list')
    for_stmt_list = vars_ | for_stmt_list0
    for_cond = expr | pp.Group(pp.empty).setName('stmt_list')
    for_body = stmt | pp.Group(SEMI).setName('stmt_list')
    for_ = FOR.suppress() + LPAR + for_stmt_list + SEMI + for_cond + SEMI + for_stmt_list + RPAR + func_body


    stmt << (
            class_init
            | func
            | vars_ + SEMI
            | func_body
    )

    func_stmt << (
            func_class_init
            | vars_ + SEMI
            | call + SEMI
            | new + SEMI
            | caller + SEMI
            | body
            | assign + SEMI
            | return_ + SEMI
            | if_
            | for_
    )

    stmt_list = pp.ZeroOrMore(stmt)
    func_stmt_list = pp.ZeroOrMore(func_stmt)

    body << LBRACE + stmt_list + RBRACE
    func_body << LBRACE + func_stmt_list + RBRACE

    class_init << (access_keys | pp.Group(pp.Empty())) + CLASS + ident + body
    func_class_init << CLASS + ident + body

    program = pp.ZeroOrMore(class_init)
    start = program

    def set_parse_action_magic(rule_name: str, parser_element: pp.ParserElement) -> None:
        if rule_name == rule_name.upper():
            return
        if getattr(parser_element, 'name', None) and parser_element.name.isidentifier():
            rule_name = parser_element.name
        cls = ''.join(x.capitalize() for x in rule_name.split('_')) + 'Node'
        with suppress(NameError):
            cls = eval(cls)
            if not inspect.isabstract(cls):
                def parse_action(s, loc, tocs):
                    if cls is FuncNode:
                        return FuncNode(tocs[0], tocs[1], tocs[2], tocs[3], tocs[4:-1], tocs[-1], loc=loc)
                    else:
                        return cls(*tocs, loc=loc)

                parser_element.setParseAction(parse_action)

    for var_name, value in locals().copy().items():
        if isinstance(value, pp.ParserElement):
            set_parse_action_magic(var_name, value)

    return start


parser = make_parser()


def parse(prog: str) -> StmtListNode:
    locs = []
    row, col = 0, 0
    for ch in prog:
        if ch == '\n':
            row += 1
            col = 0
        elif ch == '\r':
            pass
        else:
            col += 1
        locs.append((row, col))

    old_init_action = AstNode.init_action

    def init_action(node: AstNode) -> None:
        loc = getattr(node, 'loc', None)
        if isinstance(loc, int):
            node.row = locs[loc][0] + 1
            node.col = locs[loc][1] + 1

    AstNode.init_action = init_action
    try:
        prog: StmtListNode = parser.parseString(str(prog))[0]
        prog.program = True
        return prog
    finally:
        AstNode.init_action = old_init_action