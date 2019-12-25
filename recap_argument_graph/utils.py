from __future__ import absolute_import, annotations

import itertools
import uuid
import collections
import typing as t


# key_iterator = itertools.count(start=1)
#
#
# def keygen() -> int:
#     return next(key_iterator)


def unique_id() -> int:
    return uuid.uuid1().int >> 64


def xstr(data: t.Any) -> str:
    return "" if data is None else str(data)


def parse(text: str, nlp: t.Optional[t.Callable[[str], t.Any]]) -> t.Any:
    return nlp(text) if nlp else text


def type_error(actual: t.Type, expected: t.Type) -> str:
    return f"Expected type '{expected}', but got '{actual}'. Make sure that you are passing the correct method arguments."


def duplicate_key_error(name: str, key: int) -> str:
    return f"Graph '{name}' already contains an element with key '{key}'. The keys have to be unique within each graph."


def missing_key_error(name: str, key: int) -> str:
    return f"Graph '{name}' does not contain an element with key '{key}'. It cannot be removed."


# A sentinel object to detect if a parameter is supplied or not.  Use
# a class to give it a better repr.
class _MISSING_TYPE:
    pass


MISSING = _MISSING_TYPE()


T = t.TypeVar("T")
X = t.TypeVar("X")


class ImmutableList(t.Sequence[T]):
    """Read-only view."""

    _store: t.Sequence[T]

    def __init__(self, items: t.Optional[t.Sequence[T]] = None):
        self._store = items or list()

    def __len__(self) -> int:
        return self._store.__len__()

    def __getitem__(self, key: int) -> T:
        return self._store.__getitem__(key)

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __str__(self) -> str:
        return self._store.__str__()


class ImmutableSet(t.AbstractSet[T]):
    """Read-only view."""

    _store: t.AbstractSet[T]

    def __init__(self, items: t.Optional[t.AbstractSet[T]] = None):
        self._store = items or set()

    def __len__(self) -> int:
        return self._store.__len__()

    def __contains__(self, key: int) -> bool:
        return self._store.__contains__(key)

    def __iter__(self) -> t.Iterator[T]:
        return self._store.__iter__()

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __str__(self) -> str:
        return self._store.__str__()


class ImmutableDict(t.Mapping[X, T]):
    """Read-only view."""

    _store: t.Dict[X, T]

    def __init__(self, items: t.Optional[t.Dict[X, T]] = None):
        self._store = items or collections.OrderedDict()

    def __len__(self) -> int:
        return self._store.__len__()

    def __getitem__(self, key: X) -> T:
        return self._store.__getitem__(key)

    def __iter__(self) -> t.Iterator:
        return self._store.__iter__()

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __str__(self) -> str:
        return self._store.__str__()
