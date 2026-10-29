from dataclasses import KW_ONLY, dataclass

__all__ = ("Reference",)


@dataclass(slots=True, frozen=True)
class Reference:
    """Text span of a resource that an atom node is based on.

    The resource is given by its id, the offset counts code points.
    """

    text: str
    _: KW_ONLY
    resource: str | None = None
    offset: int | None = None
