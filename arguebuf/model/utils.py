import typing as t
from collections import abc
from uuid import uuid1


def uuid() -> str:
    return str(uuid1())


def _class_name(obj) -> str:
    return obj.__class__.__name__


def class_repr(obj, attributes: t.Iterable[str]) -> str:
    return f"{_class_name(obj)}({', '.join(attributes)})"


def xstr(data: t.Any) -> str:
    return "" if data is None else str(data)


def parse(text: t.Optional[str], nlp: t.Optional[t.Callable[[str], t.Any]]) -> t.Any:
    if nlp:
        if text is None:
            return nlp("")

        try:
            out = nlp(text)
        except ValueError:
            out = nlp("")

        return out

    return text


def type_error(actual: type, expected: type) -> str:
    return (
        f"Expected type '{expected}', but got '{actual}'. Make sure that you are"
        " passing the correct method arguments."
    )


def duplicate_key_error(name: str, key: str) -> str:
    return (
        f"Graph '{name}' already contains an element with key '{key}'. The keys have to"
        " be unique within each graph."
    )


def missing_key_error(name: str, key: str) -> str:
    return (
        f"Graph '{name}' does not contain an element with key '{key}'. It cannot be"
        " removed."
    )


_T = t.TypeVar("_T")
_U = t.TypeVar("_U")


class ImmutableList(abc.Sequence[_T]):
    """Read-only view."""

    __slots__ = "_store"

    _store: t.MutableSequence[_T]

    def __init__(self, items: t.Optional[t.MutableSequence[_T]] = None):
        self._store = items or []

    def __len__(self) -> int:
        return self._store.__len__()

    @t.overload
    def __getitem__(self, key: int) -> _T:
        pass  # Don't put code here

    @t.overload
    def __getitem__(self, key: slice) -> t.Sequence[_T]:
        pass  # Don't put code here

    def __getitem__(self, key: t.Union[int, slice]) -> t.Union[_T, t.Sequence[_T]]:
        return self._store.__getitem__(key)

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __str__(self) -> str:
        return self._store.__str__()


class ImmutableSet(abc.Set[_T]):
    """Read-only view."""

    __slots__ = "_store"

    _store: t.MutableSet[_T]

    def __init__(self, items: t.Optional[t.MutableSet[_T]] = None):
        self._store = items or set()

    def __len__(self) -> int:
        return self._store.__len__()

    def __contains__(self, item: object) -> bool:
        return self._store.__contains__(item)

    def __iter__(self) -> t.Iterator[_T]:
        return self._store.__iter__()

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __str__(self) -> str:
        return self._store.__str__()


class ImmutableDict(t.Mapping[_T, _U]):
    """Read-only view."""

    __slots__ = "_store"

    _store: t.MutableMapping[_T, _U]

    def __init__(self, items: t.Optional[t.MutableMapping[_T, _U]] = None):
        self._store = items or {}

    def __len__(self) -> int:
        return self._store.__len__()

    def __getitem__(self, key: _T) -> _U:
        return self._store.__getitem__(key)

    def __contains__(self, key: _T) -> bool:
        return self._store.__contains__(key)

    def __iter__(self) -> t.Iterator:
        return self._store.__iter__()

    def __repr__(self) -> str:
        return self._store.__repr__()

    def __str__(self) -> str:
        return self._store.__str__()
