from abc import ABC
from typing import override
from uuid import uuid1

__all__ = ("Entity", "uuid")


def uuid() -> str:
    return str(uuid1())


class Entity(ABC):
    """Abstract base that compares and hashes elements by their type and unique `id`."""

    __slots__ = ()

    _id: str

    @property
    def id(self) -> str:
        """Stable identifier used by graph collections and references."""
        return self._id

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
