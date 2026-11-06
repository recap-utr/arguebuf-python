"""Subset of the AIF and xAIF graph read and written by arguebuf."""

import typing as t

from ._types import Id

__all__ = (
    "DATE_FORMAT",
    "DIALOG_TYPES",
    "DialogType",
    "Edge",
    "Graph",
    "Id",
    "Locution",
    "Node",
    "NodeType",
    "Participant",
    "SchemeType",
)

type SchemeType = t.Literal["RA", "CA", "MA", "PA"]
type DialogType = t.Literal["L", "TA", "YA"]
type NodeType = SchemeType | DialogType | t.Literal["I"]
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DIALOG_TYPES: frozenset[str] = frozenset(("L", "TA", "YA"))


class Node(t.TypedDict):
    """Node of an AIF graph, unknown types are skipped by the loader."""

    nodeID: Id
    text: str
    type: str
    timestamp: t.NotRequired[str | None]
    scheme: t.NotRequired[str | None]


class Edge(t.TypedDict):
    """Edge of an AIF graph."""

    edgeID: Id
    fromID: Id
    toID: Id
    formEdgeID: t.NotRequired[Id | None]


class Locution(t.TypedDict):
    """Utterance of a participant, linked to a locution node."""

    nodeID: Id
    personID: Id


class Participant(t.TypedDict):
    """Person of a dialog."""

    participantID: Id
    firstname: t.NotRequired[str | None]
    surname: t.NotRequired[str | None]


class Graph(t.TypedDict):
    """AIF graph, also the `AIF` part of xAIF.

    The participants are only part of xAIF, AIFdb stores them separately.
    """

    nodes: list[Node]
    edges: list[Edge]
    locutions: t.NotRequired[list[Locution] | None]
    participants: t.NotRequired[list[Participant] | None]
