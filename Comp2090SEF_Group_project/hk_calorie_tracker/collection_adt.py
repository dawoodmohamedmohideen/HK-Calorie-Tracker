from __future__ import annotations

from typing import Generic, Iterable, Iterator, TypeVar


T = TypeVar("T")


class ItemCollectionADT(Generic[T]):
    """A simple list-backed ADT for ordered item storage."""

    def __init__(self, items: Iterable[T] | None = None):
        self._items = list(items or [])

    def add(self, item: T) -> None:
        self._items.append(item)

    def pop(self, index: int = -1) -> T:
        return self._items.pop(index)

    def clear(self) -> None:
        self._items.clear()

    def __iter__(self) -> Iterator[T]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: int) -> T:
        return self._items[index]
