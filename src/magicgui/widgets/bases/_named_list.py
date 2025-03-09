from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSequence
    from typing import Protocol

    class Named(Protocol):
        name: str


T = TypeVar("T", bound="Named")


class NamedList(Generic[T]):
    """Container that maintains a list of objects with a 'name' attribute,.

    Supports list-like insertion and O(1) lookup by name.
    """

    def __init__(self) -> None:
        self._list: list[T] = []
        self._dict: dict[str, T] = {}

    def insert(self, index: int, item: T) -> None:
        """Inserts an item at the specified index.

        Raises ValueError if an item with the same name already exists.
        """
        self._list.insert(index, item)
        # NB!
        # we don't actually assert name uniqueness here, because it ruins
        # the true list-like quality. So, when retrieving by name, you will
        # simply get the first item that has been inserted with that name.
        if item.name not in self._dict:
            self._dict[item.name] = item

    def append(self, item: T) -> None:
        """Appends an item at the end of the list."""
        self.insert(len(self._list), item)

    def get_by_name(self, name: str) -> T | None:
        """Returns the item with the given name, or None if not found."""
        return self._dict.get(name)

    def remove_by_name(self, name: str) -> None:
        """Removes the item with the given name."""
        item = self._dict.pop(name)
        self._list.remove(item)

    @overload
    def __getitem__(self, key: int) -> T: ...
    @overload
    def __getitem__(self, key: slice) -> MutableSequence[T]: ...
    def __getitem__(self, index: int | slice) -> T | MutableSequence[T]:
        return self._list[index]

    @overload
    def __delitem__(self, index: slice) -> None: ...
    @overload
    def __delitem__(self, index: int) -> None: ...
    def __delitem__(self, index: int | slice) -> None:
        if isinstance(index, slice):
            for item in self._list[index]:
                self._dict.pop(item.name, None)
            del self._list[index]
        else:
            item = self._list[index]
            del self._list[index]
            self._dict.pop(item.name, None)

    def __len__(self) -> int:
        return len(self._list)

    def __iter__(self) -> Iterator[T]:
        return iter(self._list)

    def __repr__(self) -> str:
        return repr(self._list)
