"""Subset of the xAIF graph read and written by arguebuf."""

import typing as t

from .aif import Graph as AifGraph

__all__ = ("Aif", "Graph", "Text")


class Aif(AifGraph):
    """`AIF` part of an xAIF graph, the fulfillments are not read by the loader."""

    schemefulfillments: t.NotRequired[list[object] | None]
    descriptorfulfillments: t.NotRequired[list[object] | None]
    cqdescriptorfulfillments: t.NotRequired[list[object] | None]


class Text(t.TypedDict):
    """HTML text wrapped in an object."""

    txt: t.NotRequired[str | None]


class Graph(t.TypedDict):
    """xAIF graph, its `text` is HTML, a missing text yields no resource."""

    AIF: Aif
    text: t.NotRequired[str | Text | None]
    dialog: t.NotRequired[bool | None]
