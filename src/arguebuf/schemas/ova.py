"""Subset of the OVA graph read by arguebuf."""

import typing as t

from pydantic import AfterValidator

from ._types import Id

__all__ = (
    "DATE_FORMAT",
    "DATE_FORMAT_ANALYSIS",
    "Analysis",
    "Edge",
    "Endpoint",
    "Graph",
    "Node",
    "Participant",
)


def _no_participant(value: str | None) -> str | None:
    """OVA stores `0` if a node has no participant."""
    return None if value == "0" else value


DATE_FORMAT = "%d/%m/%Y - %H:%M:%S"
DATE_FORMAT_ANALYSIS = "%d/%m/%Y"


class Node(t.TypedDict):
    """Node of an OVA graph, unknown types are skipped by the loader."""

    id: Id
    text: str
    type: str
    descriptors: t.NotRequired[dict[str, Id | None] | None]
    participantID: t.NotRequired[
        t.Annotated[Id | None, AfterValidator(_no_participant)]
    ]
    majorClaim: t.NotRequired[bool | None]
    date: t.NotRequired[str | None]


class Endpoint(t.TypedDict):
    """Node referenced by an edge."""

    id: Id


# `from` is a keyword and thus requires the functional syntax
Edge = t.TypedDict(
    "Edge",
    {"from": Endpoint, "to": Endpoint, "date": t.NotRequired[str | None]},
)
"""Edge of an OVA graph."""


class Participant(t.TypedDict):
    """Person of a dialog."""

    id: Id
    firstname: t.NotRequired[str | None]
    surname: t.NotRequired[str | None]


class Analysis(t.TypedDict):
    """Analyzed document and its annotation."""

    txt: t.NotRequired[str | None]
    plain_txt: t.NotRequired[str | None]
    documentDate: t.NotRequired[str | None]
    annotatorName: t.NotRequired[str | None]
    documentSource: t.NotRequired[str | None]
    documentTitle: t.NotRequired[str | None]


class Graph(t.TypedDict):
    """OVA graph."""

    nodes: list[Node]
    edges: list[Edge]
    participants: list[Participant]
    analysis: Analysis
