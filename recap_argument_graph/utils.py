from __future__ import absolute_import, annotations

import itertools
import uuid
from collections import OrderedDict
from typing import (
    Any,
    Optional,
    Callable,
    Dict,
    List,
    Sequence,
    Mapping,
    Iterator,
    Set,
    TypeVar,
)


# key_iterator = itertools.count(start=1)
#
#
# def keygen() -> int:
#     return next(key_iterator)


def unique_id() -> int:
    return uuid.uuid1().int >> 64


def xstr(data: Any) -> str:
    return "" if data is None else str(data)


def parse(text: str, nlp: Optional[Callable[[str], Any]]) -> Any:
    return nlp(text) if nlp else text


# A sentinel object to detect if a parameter is supplied or not.  Use
# a class to give it a better repr.
class _MISSING_TYPE:
    pass


MISSING = _MISSING_TYPE()


T = TypeVar("T")
X = TypeVar("X")


class ImmutableList(Sequence[T]):
    """Read-only view."""

    _store: List[T]

    def __init__(self, items: Optional[List[T]] = None):
        self._store = items or list()

    def __len__(self) -> int:
        return self._store.__len__()

    def __getitem__(self, key: int) -> T:
        return self._store.__getitem__(key)

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __str__(self) -> str:
        return self._store.__str__()


class ImmutableSet(Set[T]):
    """Read-only view."""

    _store: Set[T]

    def __init__(self, items: Optional[Set[T]] = None):
        self._store = items or set()

    def __len__(self) -> int:
        return self._store.__len__()

    def __contains__(self, key: int) -> bool:
        return self._store.__contains__(key)

    def __iter__(self) -> Iterator[T]:
        return self._store.__iter__()

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __str__(self) -> str:
        return self._store.__str__()


class ImmutableDict(Mapping[X, T]):
    """Read-only view."""

    _store: Dict[X, T]

    def __init__(self, items: Optional[Dict[X, T]] = None):
        self._store = items or OrderedDict()

    def __len__(self) -> int:
        return self._store.__len__()

    def __getitem__(self, key: X) -> T:
        return self._store.__getitem__(key)

    def __iter__(self) -> Iterator:
        return self._store.__iter__()

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __str__(self) -> str:
        return self._store.__str__()
