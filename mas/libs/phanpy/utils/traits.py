import copy
from typing import Protocol

from typing_extensions import Self


class Copyable(Protocol):
    def copy(self, deep: bool = True) -> Self: ...


class CopyTrait:
    def __deepcopy_memo__(self) -> list[int]:
        return []

    def __deepcopy__(self, memo: dict[int, object] | None = None) -> Self:
        cls = self.__class__
        obj = cls.__new__(cls)
        if memo is None:
            memo = {}

        memo[id(self)] = obj

        memos = self.__deepcopy_memo__()

        for name, value in self.__dict__.items():
            if id(value) in memos:
                setattr(obj, name, value)
            else:
                setattr(obj, name, copy.deepcopy(value, memo))

        return obj

    def copy(self, deep: bool = True) -> Self:
        return copy.deepcopy(self) if deep else copy.copy(self)
