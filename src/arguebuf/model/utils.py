from abc import ABC
from typing import override
from uuid import uuid4

__all__ = ("Entity", "id_of", "uuid")


def uuid() -> str:
    """A new random id, a UUID of version 4."""
    return str(uuid4())


class Entity(ABC):
    """Abstract base that compares and hashes elements by their type and unique `id`."""

    __slots__ = ()

    id: str
    """Stable identifier used by graph collections and references."""

    @override
    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Entity)
            and type(self) is type(other)
            and self.id == other.id
        )

    @override
    def __hash__(self) -> int:
        return hash(self.id)

    @override
    def __str__(self) -> str:
        return self.id



def id_of(element: str | Entity) -> str:
    """Id of an element that is given by itself or its id."""
    return element if isinstance(element, str) else element.id
