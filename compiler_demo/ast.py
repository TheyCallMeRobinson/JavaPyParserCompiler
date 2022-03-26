from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Optional, Union, Tuple, Callable

from .semantic import TypeDesc, IdentDesc, AccessType

TYPES = {"int": "Integer", "float": "Float", "double": "Double", "boolean": "Boolean", "short": "Short", "char": "Char",
         "long": "Long", "byte": "Byte"}


class AstNode(ABC):
    """Базовый абстрактый класс узла AST-дерева"""

    init_action: Callable[['AstNode'], None] = None

    def __init__(self, row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__()
        self.row = row
        self.col = col
        for k, v in props.items():
            setattr(self, k, v)
        if AstNode.init_action is not None:
            AstNode.init_action(self)
        self.node_type: Optional[TypeDesc] = None
        self.node_ident: Optional[IdentDesc] = None
        self.await_names = []
        self.type_changing = []
        self.is_async = False
        self.external_await_names = []
        self.external_type_changing = []

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return ()

    def to_str(self):
        return str(self)

    def to_str_full(self):
        r = ''
        if self.node_ident:
            r = str(self.node_ident)
        elif self.node_type:
            r = str(self.node_type)
        return self.to_str() + (' : ' + r if r else '')

    @property
    def tree(self) -> [str, ...]:
        r = [self.to_str_full()]
        childs = self.childs
        for i, child in enumerate(childs):
            ch0, ch = '├', '│'
            if i == len(childs) - 1:
                ch0, ch = '└', ' '
            r.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return tuple(r)

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None


class _GroupNode(AstNode):
    """Класс для группировки других узлов (вспомогательный, в синтаксисе нет соотвествия)
    """

    def __init__(self, name: str, *childs: AstNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.name = name
        self._childs = childs

    def __str__(self) -> str:
        return self.name

    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return self._childs



class ExprNode(AstNode, ABC):
    """Абстракный класс для выражений в AST-дереве
    """



class LiteralNode(ExprNode):
    """Класс для представления в AST-дереве литералов (числа, строки, логическое значение)
    """

    def __init__(self, literal: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.literal = literal
        if literal in ('true', 'false'):
            self.value = bool(literal)
        else:
            self.value = eval(literal)

    def __str__(self) -> str:
        return self.literal



class IdentNode(ExprNode):
    """Класс для представления в AST-дереве идентификаторов
    """

    def __init__(self, name: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)



class TypeNode(IdentNode):
    """Класс для представления в AST-дереве типов данный
       (при появлении составных типов данных должен быть расширен)
    """

    def __init__(self, name: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(name, row=row, col=col, **props)
        self.type = None
        with suppress(ValueError):
            self.type = TypeDesc.from_str(name)

    def to_str_full(self):
        return self.to_str()


    def await_names_check(self):
        return [], []


class AccessNode(IdentNode):

    def __init__(self, name: str,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(name, row=row, col=col, **props)
        self.type = None
        with suppress(ValueError):
            self.type = AccessType.from_str(name)

    def to_str_full(self):
        return self.to_str()


    def await_names_check(self):
        return [], []


class CallNode(ExprNode):
    """Класс для представления в AST-дереве вызова функций
       (в языке программирования может быть как expression, так и statement)
    """

    def __init__(self, func: IdentNode, *params: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.func = func
        self.params = params

    def __str__(self) -> str:
        return 'call'

    def await_names_check(self):
        return [], []

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self.func, _GroupNode('params', *self.params)


class CallerNode(ExprNode):
    """Класс для представления в AST-дереве вызова функций
       (в языке программирования может быть как expression, так и statement)
    """

    def __init__(self, call: CallNode, expr: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.call = call
        self.expr = expr

    def __str__(self) -> str:
        return 'call'

    def is_await(self):
        if isinstance(self.childs[1], CallNode) and self.childs[1].col == "await":
            return True
        else:
            return False

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return _GroupNode(str(self.call)), self.expr

    def await_names_check(self):
        return [], []


class TypeConvertNode(ExprNode):
    """Класс для представления в AST-дереве операций конвертации типов данных
       (в языке программирования может быть как expression, так и statement)
    """

    def __init__(self, expr: ExprNode, type_: TypeDesc,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.expr = expr
        self.type = type_
        self.node_type = type_

    def __str__(self) -> str:
        return 'convert'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return (_GroupNode(str(self.type), self.expr),)


class StmtNode(ExprNode, ABC):
    """Абстракный класс для деклараций или инструкций в AST-дереве
    """

    def to_str_full(self):
        return self.to_str()

    def await_names_check(self):
        return [], []


class FuncStmtNode(ExprNode, ABC):
    """Абстракный класс для деклараций или инструкций в AST-дереве
    """

    def to_str_full(self):
        return self.to_str()


class AssignNode(ExprNode):
    """Класс для представления в AST-дереве оператора присваивания
    """

    def __init__(self, var: IdentNode, val: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.var = var
        self.val = val

    def __str__(self) -> str:
        return '='

    def await_names_check(self):
        if self.childs[1].is_await():
            return [self.childs[0].name], [self.childs[0].name]
        else:
            return [], []

    @property
    def childs(self) -> Tuple[IdentNode, ExprNode]:
        return self.var, self.val


class VarsNode(StmtNode):
    """Класс для представления в AST-дереве объявления переменнных
    """

    def __init__(self, type_: TypeNode, *vars_: Union[IdentNode, 'AssignNode'],
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.type = type_
        self.vars = vars_

    def __str__(self) -> str:
        return str(self.type)

    def await_names_check(self):
        result, type_change = [], []
        for i in self.childs:
            if isinstance(i, AssignNode):
                if i.childs[1].call == 'await':
                    self.is_async = True
                    type_change.append(i.childs[0].name)
                    result.append(i.childs[0].name)
                tmp_result, tmp_type_change = i.await_names_check()
                result.extend(tmp_result)
                type_change.extend(tmp_type_change)

        return result, type_change

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self.vars


class NewNode(StmtNode):
    """Класс для представления в AST-дереве оператора return
    """

    def __init__(self, val: CallNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.val = val

    def __str__(self) -> str:
        return 'new '

    def await_names_check(self):
        return [], []

    @property
    def childs(self) -> Tuple[ExprNode]:
        return (self.val,)


class ReturnNode(StmtNode):
    """Класс для представления в AST-дереве оператора return
    """

    def __init__(self, val: ExprNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.val = val

    def __str__(self) -> str:
        return 'return'

    @property
    def childs(self) -> Tuple[ExprNode]:
        return (self.val,)

    def await_names_check(self, is_await):
        return [], []


class IfNode(StmtNode):
    """Класс для представления в AST-дереве условного оператора
    """

    def __init__(self, cond: ExprNode, then_stmt: StmtNode, else_stmt: Optional[StmtNode] = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.cond = cond
        self.then_stmt = then_stmt
        self.else_stmt = else_stmt

        self.await_names = []
        self.type_changing = []
        self.is_async = []
        self.external_await_names = []
        self.await_names = []

    def __str__(self) -> str:
        return 'if'

    def await_names_check(self):
        result, type_change = [], []
        for x in self.childs:
            tmp_result, tmp_type_change = x.await_names_check()
            result.extend(tmp_result)
            type_change.extend(tmp_type_change)
        return result, type_change

    @property
    def childs(self) -> Tuple[ExprNode, StmtNode, Optional[StmtNode]]:
        return (self.cond, self.then_stmt, *((self.else_stmt,) if self.else_stmt else tuple()))


class ForNode(StmtNode):
    """Класс для представления в AST-дереве цикла for
    """

    def __init__(self, init: Optional[StmtNode], cond: Optional[ExprNode],
                 step: Optional[StmtNode], body: Optional[StmtNode],
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.init = init if init else EMPTY_STMT
        self.cond = cond if cond else EMPTY_STMT
        self.step = step if step else EMPTY_STMT
        self.body = body if body else EMPTY_STMT

    def __str__(self) -> str:
        return 'for'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self.init, self.cond, self.step, self.body

    def await_names_check(self):
        result, type_change = [], []
        for x in self.childs:
            tmp_result, tmp_type_change = x.await_names_check()
            result.extend(tmp_result)
            type_change.extend(tmp_type_change)
        return result, type_change


class ParamNode(StmtNode):
    """Класс для представления в AST-дереве объявления параметра функции
    """

    def __init__(self, type_: TypeNode, name: IdentNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.type = type_
        self.name = name

    def __str__(self) -> str:
        return str(self.type)

    @property
    def childs(self) -> Tuple[IdentNode]:
        return self.name,


class FuncNode(StmtNode):
    """Класс для представления в AST-дереве объявления функции
    """

    def __init__(self, async_: AccessNode, access: AccessNode, static: AccessNode, type_: TypeNode, name: IdentNode,
                 params: Tuple[ParamNode], body: Optional[StmtNode] = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.async_ = async_
        self.access = access if access else empty_access
        self.static = static
        self.type = type_
        self.name = name
        self.params = params
        self.body = body

    def __str__(self) -> str:
        return 'function'

    def await_names_check(self):
        if self.async_ == "async":
            self.await_names.extend([x.name.name for x in self.params])
            tmp_result, temp_type_change = self.body.await_names_check(True)
        else:
            tmp_result, temp_type_change = self.body.await_names_check(False)
        self.await_names.extend(tmp_result)
        self.type_changing.extend(temp_type_change)

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return _GroupNode(str(self.async_),
                          _GroupNode(str(self.access),
                                     _GroupNode(str(self.static),
                                                _GroupNode(str(self.type),
                                                           self.name),
                                                ))), _GroupNode('params', *self.params), self.body


class StmtListNode(StmtNode):
    """Класс для представления в AST-дереве последовательности инструкций
    """

    def __init__(self, *exprs: StmtNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.exprs = exprs
        self.program = False

    def __str__(self) -> str:
        return '...'

    @property
    def childs(self) -> Tuple[StmtNode, ...]:
        return self.exprs

    def await_names_check(self):
        result = []
        type_change = []
        for x in self.childs:
            if isinstance(x, FuncNode):
                x.await_names_check()
            else:
                tmp_result, tmp_type_change = x.await_names_check()
                result.extend(tmp_result)
                type_change.extend(tmp_type_change)
        return result, type_change


class FuncStmtListNode(StmtNode):
    """Класс для представления в AST-дереве последовательности инструкций
    """

    def __init__(self, *exprs: StmtNode,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.exprs = exprs
        self.program = False

    def __str__(self) -> str:
        return '...'

    def await_names_check(self, *args):
        result, type_change = [], []
        for x in self.exprs:
            if isinstance(x, ReturnNode):
                tmp_result, tmp_type_change = x.await_names_check(args[0])
            else :
                tmp_result, tmp_type_change = x.await_names_check()
            result.extend(tmp_result)
            type_change.extend(tmp_type_change)
        return result, type_change

    @property
    def childs(self) -> Tuple[StmtNode, ...]:
        return self.exprs


EMPTY_STMT = StmtListNode()
EMPTY_IDENT = IdentDesc('', TypeDesc.VOID)


class ClassInitNode(StmtNode):
    """Класс для представления в AST-дереве объявления функции
    """

    def __init__(self, access: AccessNode, name: IdentNode, body: Optional[StmtListNode] = None,
                 row: Optional[int] = None, col: Optional[int] = None, **props) -> None:
        super().__init__(row=row, col=col, **props)
        self.access = access if access else empty_access
        self.name = name
        self.body = body if body else empty_statement_list

    def __str__(self) -> str:
        return 'class'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return _GroupNode(str(self.access), self.name), self.body


empty_statement_list = StmtListNode()
empty_access = AccessNode("")
