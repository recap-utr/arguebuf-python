from dataclasses import dataclass, field
from datetime import datetime

from arguebuf.dt import now

__all__ = ("Metadata",)


@dataclass(slots=True, frozen=True)
class Metadata:
    """Creation and modification timestamps of an element."""

    created: datetime = field(default_factory=now)
    updated: datetime = field(default_factory=now)
