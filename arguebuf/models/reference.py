from __future__ import annotations

import typing as t


from arguebuf.models.resource import Resource
from arguebuf.services import utils


class Reference:
    _resource: t.Optional[Resource]
    offset: t.Optional[int]
    text: t.Any

    def __init__(
        self,
        resource: t.Optional[Resource] = None,
        offset: t.Optional[int] = None,
        text: t.Optional[t.Any] = None,
    ) -> None:
        self._resource = resource
        self.offset = offset
        self.text = text

    @property
    def plain_text(self) -> str:
        """Generate a string from Resource object."""
        return utils.xstr(self.text)

    @property
    def resource(self) -> t.Optional[Resource]:
        return self._resource
