from dataclasses import KW_ONLY, dataclass, field

from arguebuf.model.userdata import Userdata
from arguebuf.model.utils import Entity, uuid

__all__ = ("Analyst",)


@dataclass(slots=True, frozen=True, eq=False)
class Analyst(Entity):
    """Person who annotated the argument graph."""

    name: str | None = None
    _: KW_ONLY
    email: str | None = None
    userdata: Userdata = field(default_factory=dict, repr=False)
    id: str = field(default_factory=uuid)
