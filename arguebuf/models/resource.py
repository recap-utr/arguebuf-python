from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from pendulum.datetime import DateTime

from arguebuf.models.metadata import Metadata
from arguebuf.models.userdata import Userdata
from arguebuf.services import utils


@dataclass()
class Resource:
    text: t.Any
    title: t.Optional[str] = None
    source: t.Optional[str] = None
    timestamp: t.Optional[DateTime] = None
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
