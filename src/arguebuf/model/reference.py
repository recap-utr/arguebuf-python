from dataclasses import KW_ONLY, dataclass

from arguebuf.locate import is_anchored

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

    def span(self, source: str) -> tuple[int, int] | None:
        """The start and end index of the text in the source, if it is found at its offset.

        Examples:
            >>> Reference("cats", offset=4).span("Big cats purr.")
            (4, 8)
            >>> Reference("cats", offset=0).span("Big cats purr.") is None
            True
        """
        offset = self.offset

        if offset is None or not is_anchored(source, self.text, offset):
            return None

        return offset, offset + len(self.text)
