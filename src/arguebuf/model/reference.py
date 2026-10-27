from dataclasses import KW_ONLY, dataclass

from arguebuf.model.resource import AbstractResource

__all__ = ("Reference",)


@dataclass(slots=True, frozen=True)
class Reference:
    """Text span of a resource that an atom node is based on."""

    text: str
    _: KW_ONLY
    resource: AbstractResource | None = None
    offset: int | None = None
