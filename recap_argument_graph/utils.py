from __future__ import absolute_import, annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Optional, Callable, Dict, List, Sequence, Mapping, Iterable

import typing


def unique_id() -> int:
    return uuid.uuid1().int >> 64


def xstr(data: Any) -> str:
    return "" if data is None else str(data)


def parse(text: str, nlp: Optional[Callable[[str], Any]]) -> Any:
    return nlp(text) if nlp else text


T = typing.TypeVar("T")
X = typing.TypeVar("X")


@dataclass(order=True)
class ImmutableList(Sequence[T]):
    """Read-only view."""

    _store: List[T] = field(default_factory=list)

    def __len__(self) -> int:
        return self._store.__len__()

    def __getitem__(self, key: int) -> T:
        return self._store.__getitem__(key)

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __str__(self) -> str:
        return self._store.__str__()


@dataclass(order=True)
class ImmutableDict(Mapping[X, T]):
    """Read-only view."""

    _store: Dict[X, T] = field(default_factory=dict)

    def __len__(self) -> int:
        return self._store.__len__()

    def __getitem__(self, key: X) -> T:
        return self._store.__getitem__(key)

    def __iter__(self) -> Iterable:
        return self._store.__iter__()

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __str__(self) -> str:
        return self._store.__str__()
