"""SQLite 兼容枚举：存储 value（moe），读取时兼容旧数据 name（MOE）"""
import enum
from typing import TypeVar

from sqlalchemy import String
from sqlalchemy.types import TypeDecorator

E = TypeVar("E", bound=enum.Enum)


class StrEnumType(TypeDecorator):
    impl = String(32)
    cache_ok = True

    def __init__(self, enum_cls: type[E], length: int = 32):
        self.enum_cls = enum_cls
        super().__init__(length=length)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, self.enum_cls):
            return value.value
        if isinstance(value, str) and value in self.enum_cls.__members__:
            return self.enum_cls[value].value
        return str(value)

    def process_result_value(self, value, dialect) -> E | None:
        if value is None:
            return None
        if isinstance(value, self.enum_cls):
            return value
        text = str(value)
        try:
            return self.enum_cls(text)
        except ValueError:
            pass
        if text in self.enum_cls.__members__:
            return self.enum_cls[text]
        lower = text.lower()
        try:
            return self.enum_cls(lower)
        except ValueError:
            return list(self.enum_cls)[0]


def enum_column(enum_cls: type[E], **kwargs) -> StrEnumType:
    return StrEnumType(enum_cls, **kwargs)
