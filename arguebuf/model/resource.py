import typing as t
from dataclasses import dataclass, field

import pendulum

from arguebuf.model import utils
from arguebuf.model.metadata import Metadata
from arguebuf.model.userdata import Userdata

__all__ = ("Resource",)


@dataclass()
class Resource:
    text: t.Any
    title: str | None = None
    source: str | None = None
    timestamp: pendulum.DateTime | None = None
    metadata: Metadata = field(default_factory=Metadata)
    userdata: Userdata = field(default_factory=dict)
    _id: str = field(default_factory=utils.uuid)

    @property
    def id(self) -> str:
        return self._id

    @property
    def plain_text(self) -> str:
        """Generate a string from Resource object."""
        return utils.xstr(self.text)
