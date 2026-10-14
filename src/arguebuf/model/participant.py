from dataclasses import KW_ONLY, dataclass, field

from arguebuf.model.metadata import Metadata
from arguebuf.model.userdata import Userdata
from arguebuf.model.utils import Entity, uuid

__all__ = ("Participant",)


@dataclass(slots=True, frozen=True, eq=False)
class Participant(Entity):
    """Person who authored atom nodes of the argument graph."""

    name: str | None = None
    _: KW_ONLY
    username: str | None = None
    email: str | None = None
    url: str | None = None
    location: str | None = None
    description: str | None = None
    metadata: Metadata = field(default_factory=Metadata, repr=False)
    userdata: Userdata = field(default_factory=dict, repr=False)
    id: str = field(default_factory=uuid)
