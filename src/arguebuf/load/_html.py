"""Minimal HTML walker for the highlighted texts of OVA and xAIF.

Only `span` and `br` elements are interpreted, other tags only contribute their text.
Raw text elements such as `script` are not supported.
"""

from dataclasses import dataclass
from html.parser import HTMLParser
from typing import override

__all__ = ("Span", "parse_html")


@dataclass(slots=True, frozen=True)
class Span:
    """Text of a `<span>` element and its offset in the parsed text."""

    text: str
    offset: int


class _Walker(HTMLParser):
    """Collect the text chunks of an HTML fragment and the ranges of its spans."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self.length = 0
        # ids of the open spans, None for spans that do not own an id
        self.stack: list[str | None] = []
        self.starts: dict[str, int] = {}
        self.ends: dict[str, int] = {}

    def _close(self) -> None:
        if (id := self.stack.pop()) is not None:
            self.ends[id] = self.length

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "br":
            self.handle_data("\n")
        elif tag == "span":
            # the first id attribute wins
            id = next((value for key, value in attrs if key == "id"), None)

            # the first opened span wins for duplicate ids, like a pre-order tree walk
            if id and id not in self.starts:
                self.starts[id] = self.length
                self.stack.append(id)
            else:
                self.stack.append(None)

    @override
    def handle_endtag(self, tag: str) -> None:
        if tag == "span" and self.stack:
            self._close()

    @override
    def handle_data(self, data: str) -> None:
        self.chunks.append(data)
        self.length += len(data)

    @override
    def close(self) -> None:
        super().close()

        while self.stack:
            self._close()


def parse_html(text: str) -> tuple[str, dict[str, Span]]:
    """Get the plain text of an HTML fragment and its spans by their `id`.

    Newlines are normalized, character references are decoded, `<br>` becomes a newline,
    and other tags only contribute their text.
    Unclosed spans end with the text, the first opened span wins for duplicate ids,
    and the first `id` attribute of a span wins, spans with an empty id are ignored.

    Examples:
        >>> parse_html('a <span id="n1">b &amp; c</span><br><span>d</span>')
        ('a b & c\\nd', {'n1': Span(text='b & c', offset=2)})
    """
    walker = _Walker()
    # newline normalization of the HTML input stream
    walker.feed(text.replace("\r\n", "\n").replace("\r", "\n"))
    walker.close()
    plain = "".join(walker.chunks)

    return plain, {
        id: Span(plain[start : walker.ends[id]], start)
        for id, start in walker.starts.items()
    }
