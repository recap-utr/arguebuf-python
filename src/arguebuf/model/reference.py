from dataclasses import KW_ONLY, dataclass

from arguebuf.model.resource import Resource
from arguebuf.model.utils import xstr

__all__ = ("Reference",)


@dataclass(slots=True, frozen=True)
class Reference[T = str]:
    """Text span of a resource that an atom node is based on."""

    text: T
    _: KW_ONLY
    resource: Resource[T] | None = None
    offset: int | None = None

    @property
    def plain_text(self) -> str:
        return xstr(self.text)
