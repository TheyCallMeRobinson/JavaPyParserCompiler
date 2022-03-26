from typing import Tuple, Any, Dict, Optional
from enum import Enum


# по идее, должен быть описан в ast, но возникают проблемы с cross импортом модулей, с которыми пока лень разбираться
class BinOp(Enum):
    """Перечисление возможных биранных операций
    """
    DOT = '.'
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'
    GT = '>'
    LT = '<'
    GE = '>='
    LE = '<='
    EQUALS = '=='
    NEQUALS = '!='
    LOGICAL_AND = '&&'
    LOGICAL_OR = '||'

    def __str__(self):
        return self.value


class BaseType(Enum):
    """Перечисление для базовых типов данных
    """

    VOID = 'void'
    INT = 'int'
    FLOAT = 'float'
    BOOL = 'bool'
    STR = 'string'

    def __str__(self):
        return self.value


VOID, INT, FLOAT, BOOL, STR = BaseType.VOID, BaseType.INT, BaseType.FLOAT, BaseType.BOOL, BaseType.STR


class AccessType(Enum):
    PUBLIC: 'AccessType'
    PROTECTED: 'AccessType'
    PRIVATE: 'AccessType'
    PACKAGE_PRIVATE: 'AccessType'

    def __init__(self, base_type_: Optional[BaseType] = None,
                 return_type: Optional['AccessType'] = None, params: Optional[Tuple['AccessType']] = None) -> None:
        self.base_type = base_type_
        self.return_type = return_type
        self.params = params

    def __str__(self):
        return self.value

    @staticmethod
    def from_str(str_decl: str) -> 'AccessType':
        base_type_ = BaseType(str_decl)
        return AccessType.from_base_type(base_type_)


class TypeDesc:
    """Класс для описания типа данных.

       Сейчас поддерживаются только примитивные типы данных и функции.
       При поддержки сложных типов (массивы и т.п.) должен быть рассширен
    """

    VOID: 'TypeDesc'
    INT: 'TypeDesc'
    FLOAT: 'TypeDesc'
    BOOL: 'TypeDesc'
    STR: 'TypeDesc'

    def __init__(self, base_type_: Optional[BaseType] = None,
                 return_type: Optional['TypeDesc'] = None, params: Optional[Tuple['TypeDesc']] = None) -> None:
        self.base_type = base_type_
        self.return_type = return_type
        self.params = params

    @property
    def func(self) -> bool:
        return self.return_type is not None

    @property
    def is_simple(self) -> bool:
        return not self.func

    @staticmethod
    def from_base_type(base_type_: BaseType) -> 'TypeDesc':
        return getattr(TypeDesc, base_type_.name)

    @staticmethod
    def from_str(str_decl: str) -> 'TypeDesc':
        base_type_ = BaseType(str_decl)
        return TypeDesc.from_base_type(base_type_)

    def __str__(self) -> str:
        if not self.func:
            return str(self.base_type)
        else:
            res = str(self.return_type)
            res += ' ('
            for param in self.params:
                if res[-1] != '(':
                    res += ', '
                res += str(param)
            res += ')'
        return res


for base_type in BaseType:
    setattr(TypeDesc, base_type.name, TypeDesc(base_type))


class ScopeType(Enum):
    """Перечисление для "области" декларации переменных
    """

    GLOBAL = 'global'
    GLOBAL_LOCAL = 'global.local'  # переменные относятся к глобальной области, но описаны в скобках (теряем имена)
    PARAM = 'param'
    LOCAL = 'local'

    def __str__(self):
        return self.value


class IdentDesc:
    """Класс для описания переменых
    """

    def __init__(self, name: str, type_: TypeDesc, scope: ScopeType = ScopeType.GLOBAL, index: int = 0) -> None:
        self.name = name
        self.type = type_
        self.scope = scope
        self.index = index
        self.built_in = False

    def __str__(self) -> str:
        return '{}, {}, {}'.format(self.type, self.scope, 'built-in' if self.built_in else self.index)
