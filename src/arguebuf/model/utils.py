from abc import ABC
from uuid import uuid1

__all__ = ("Entity", "uuid", "xstr")


def uuid() -> str:
    return str(uuid1())


def xstr(data: object) -> str:
    return "" if data is None else str(data)


class Entity(ABC):
    """Abstract base that compares and hashes elements by their unique `id`."""

    __slots__ = ()

    id: str

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Entity) and self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        return self.id
