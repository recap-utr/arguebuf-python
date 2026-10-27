from dataclasses import dataclass
from datetime import datetime

from arguebuf.dt import now

__all__ = ("Metadata",)


@dataclass(slots=True, frozen=True, init=False)
class Metadata:
    """Creation and modification timestamps of an element.

    `created` defaults to now and `updated` defaults to `created`,
    so both describe the same instant unless given explicitly.

    Examples:
        >>> metadata = Metadata()
        >>> metadata.created == metadata.updated
        True
    """

    created: datetime
    updated: datetime

    def __init__(
        self, created: datetime | None = None, updated: datetime | None = None
    ) -> None:
        created = created or now()
        # frozen dataclasses can only be initialized via object.__setattr__
        object.__setattr__(self, "created", created)
        object.__setattr__(self, "updated", updated or created)
