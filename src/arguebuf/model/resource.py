from dataclasses import KW_ONLY, dataclass, field
from datetime import datetime

from arguebuf.model.metadata import Metadata
from arguebuf.model.userdata import Userdata
from arguebuf.model.utils import Entity, uuid, xstr

__all__ = ("Resource",)


@dataclass(slots=True, eq=False)
class Resource[T = str](Entity):
    """Source document that atom nodes may reference."""

    text: T
    _: KW_ONLY
    title: str | None = None
    source: str | None = None
    timestamp: datetime | None = None
    metadata: Metadata = field(default_factory=Metadata, repr=False)
    userdata: Userdata = field(default_factory=dict, repr=False)
    id: str = field(default_factory=uuid)

    @property
    def plain_text(self) -> str:
        return xstr(self.text)
