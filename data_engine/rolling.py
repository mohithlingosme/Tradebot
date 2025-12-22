from __future__ import annotations

"""Generic rolling window built on top of deque."""

from collections import deque
from typing import Deque, Generic, Iterable, Iterator, List, Optional, TypeVar, Union

Number = Union[int, float]
T = TypeVar("T")


class RollingWindow(Generic[T]):
    """Fixed-size rolling window."""

    def __init__(self, maxlen: int):
        if maxlen <= 0:
            raise ValueError("maxlen must be positive")
        self._maxlen = maxlen
        self._buffer: Deque[T] = deque(maxlen=maxlen)

    def append(self, item: T) -> None:
        self._buffer.append(item)

    def extend(self, items: Iterable[T]) -> None:
        for item in items:
            self.append(item)

    def as_list(self) -> List[T]:
        return list(self._buffer)

    def __len__(self) -> int:
        return len(self._buffer)

    def __iter__(self) -> Iterator[T]:
        return iter(self._buffer)

    @property
    def maxlen(self) -> int:
        return self._maxlen

    @property
    def last(self) -> Optional[T]:
        if not self._buffer:
            return None
        return self._buffer[-1]
