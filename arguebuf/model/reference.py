import typing as t

from arguebuf.model import utils
from arguebuf.model.resource import Resource

__all__ = ("Reference",)


class Reference:
    _resource: Resource | None
    offset: int | None
    text: t.Any

    def __init__(
        self,
        resource: Resource | None = None,
        offset: int | None = None,
        text: t.Any | None = None,
    ) -> None:
        self._resource = resource
        self.offset = offset
        self.text = text

    @property
    def plain_text(self) -> str:
        """Generate a string from Resource object."""
        return utils.xstr(self.text)

    @property
    def resource(self) -> Resource | None:
        return self._resource
