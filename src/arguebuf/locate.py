"""Fuzzy search of quotes in texts."""

import functools
import math
from dataclasses import dataclass
from typing import Final

from fuzzysearch.levenshtein import find_near_matches_levenshtein

__all__ = ("DEFAULT_THRESHOLD", "Match", "is_anchored", "locate")

DEFAULT_THRESHOLD: Final = 0.85
"""Default minimal similarity of `locate`."""


@dataclass(slots=True, frozen=True)
class Match:
    """Span of a source text.

    Attributes:
        offset: Start of the span in code points.
        text: Text of the span.
        similarity: One minus the edit distance of the normalized texts
            relative to the query length.
    """

    offset: int
    text: str
    similarity: float


def _normalize(text: str) -> tuple[tuple[str, ...], tuple[int, ...]]:
    """Lowercase the words of the text and replace the gaps between them by a single space.

    Words consist of letters and digits.
    Returns the normalized characters and the code point index of the text each one stems from.
    """
    chars: list[str] = []
    origin: list[int] = []
    last: int | None = None

    for index, char in enumerate(text):
        if not char.isalnum():
            continue

        if last is not None and index > last + 1:
            chars.append(" ")
            origin.append(last + 1)

        for lowered in char.lower():
            chars.append(lowered)
            origin.append(index)

        last = index

    return tuple(chars), tuple(origin)


# sources are searched repeatedly, e.g. for every atom of a resource
_normalize_source = functools.lru_cache(maxsize=8)(_normalize)


def _exact(source: str, query: str, near: int | None) -> Match | None:
    index = source.find(query)

    if index == -1:
        return None

    if near is None:
        return Match(index, query, 1)

    offsets: list[int] = []

    while index != -1:
        offsets.append(index)
        index = source.find(query, index + 1)

    return Match(min(offsets, key=lambda offset: abs(offset - near)), query, 1)


def _approximate(
    source: str, query: str, threshold: float, near: int | None
) -> Match | None:
    pattern = _normalize(query)[0]

    if not pattern:
        return None

    chars, origin = _normalize_source(source)

    if not chars or threshold > 1:
        return None

    # Use the unconsolidated results so overlapping matches survive the proximity preference.
    maximum = min(len(pattern) - 1, math.ceil((1 - threshold) * len(pattern)))
    candidates = [
        match
        for match in find_near_matches_levenshtein(pattern, chars, maximum)
        if match.start < match.end and 1 - match.dist / len(pattern) >= threshold
    ]

    if not candidates:
        return None

    match = min(
        candidates,
        key=lambda match: (
            match.dist,
            abs(origin[match.start] - near)
            if near is not None
            else origin[match.start],
            origin[match.start],
            -match.end,
        ),
    )
    offset = origin[match.start]

    return Match(
        offset,
        source[offset : origin[match.end - 1] + 1],
        1 - match.dist / len(pattern),
    )


def locate(
    source: str,
    query: str,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    near: int | None = None,
) -> Match | None:
    """Find the span of `source` that matches `query` best.

    Exact matches are preferred, otherwise both texts are reduced to their lowercase words
    and the span with the lowest edit distance is chosen.

    Args:
        source: Text to search in.
        query: Quote to search for.
        threshold: Minimal similarity between the query and the span, from 0 to 1.
        near: Preferred offset in code points among equally similar spans.

    Returns:
        The best span or None if its similarity is below the threshold.

    Examples:
        >>> text = "Cats are the best pets. They are independent."
        >>> locate(text, "they are independant")
        Match(offset=24, text='They are independent', similarity=0.95)
    """
    if not query:
        return None

    return _exact(source, query, near) or _approximate(source, query, threshold, near)


def is_anchored(source: str, text: str, offset: int | None) -> bool:
    """Whether the text is found at the offset (in code points) of the source."""
    return offset is not None and source.startswith(text, offset)
