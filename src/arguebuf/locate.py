"""Fuzzy search of quotes in texts."""

import functools
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

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


def _distances(
    text: Sequence[str], pattern: Sequence[str], anchored: bool
) -> tuple[list[int], int]:
    """Edit distance of the pattern to the best span ending at each position of the text.

    Uses Myers' bit-parallel algorithm.
    If `anchored`, spans must start at the beginning of the text.
    Returns the distances and their minimum, which is the pattern length for an empty text.
    """
    width = len(pattern)
    full = (1 << width) - 1
    last = 1 << (width - 1)
    peq: dict[str, int] = {}

    for index, char in enumerate(pattern):
        peq[char] = peq.get(char, 0) | (1 << index)

    pv, mv, score = full, 0, width
    scores: list[int] = []
    minimum = width

    for char in text:
        eq = peq.get(char, 0)
        xv = eq | mv
        xh = (((eq & pv) + pv) ^ pv) | eq
        ph = mv | (~(xh | pv) & full)
        mh = pv & xh

        if ph & last:
            score += 1
        elif mh & last:
            score -= 1

        shifted = ((ph << 1) | int(anchored)) & full
        pv = ((mh << 1) & full) | (~(xv | shifted) & full)
        mv = shifted & xv
        scores.append(score)
        minimum = min(minimum, score)

    return scores, minimum


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
    ends, distance = _distances(chars, pattern, False)
    similarity = 1 - distance / len(pattern)

    # an empty source has no span even if the threshold permits no similarity at all
    if not ends or similarity < threshold:
        return None

    # consecutive ends of equal distance belong to the same span, its longest version is kept
    candidates = [
        index
        for index, value in enumerate(ends)
        if value == distance and (index + 1 == len(ends) or ends[index + 1] != distance)
    ]
    # spans of equal distance are compared by the start they would have without edits
    end = (
        candidates[0]
        if near is None
        else min(
            candidates,
            key=lambda index: abs(origin[max(0, index - len(pattern) + 1)] - near),
        )
    )
    # the shortest span ending at `end` with the same distance,
    # it is at most `distance` chars longer than the pattern
    window = chars[max(0, end + 1 - len(pattern) - distance) : end + 1]
    starts = _distances(window[::-1], pattern[::-1], True)[0]
    offset = origin[end - starts.index(distance)]

    return Match(offset, source[offset : origin[end] + 1], similarity)


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
