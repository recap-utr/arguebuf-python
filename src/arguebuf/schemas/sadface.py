"""Subset of the SADFace graph read by arguebuf."""

import typing as t

from arguebuf.model.userdata import JsonObject

from ._types import Id

__all__ = ("Core", "Edge", "Graph", "Metadata", "Node", "Resource", "Source")


class Source(t.TypedDict):
    """Passage of a resource."""

    resource_id: Id
    text: str
    offset: t.NotRequired[int | None]


class Node(t.TypedDict):
    """Node of a SADFace graph, unknown types are skipped by the loader.

    The type `scheme` is the generic type of older versions, it is refined by its name.
    """

    id: Id
    type: str
    text: t.NotRequired[str | None]
    name: t.NotRequired[str | None]
    sources: t.NotRequired[list[Source] | None]
    metadata: t.NotRequired[JsonObject | None]


class Edge(t.TypedDict):
    """Edge of a SADFace graph."""

    id: Id
    source_id: Id
    target_id: Id


class Resource(t.TypedDict):
    """Source document."""

    id: Id
    content: t.NotRequired[str | None]
    metadata: t.NotRequired[JsonObject | None]


class Core(t.TypedDict):
    """Metadata of the graph."""

    version: t.NotRequired[str | None]
    analyst_email: t.NotRequired[str | None]
    analyst_name: t.NotRequired[str | None]
    created: t.NotRequired[str | None]
    edited: t.NotRequired[str | None]
    description: t.NotRequired[str | None]
    notes: t.NotRequired[str | None]
    title: t.NotRequired[str | None]


class Metadata(t.TypedDict):
    """Container of the core metadata."""

    core: Core


class Graph(t.TypedDict):
    """SADFace graph."""

    nodes: list[Node]
    edges: list[Edge]
    metadata: Metadata
    resources: t.NotRequired[list[Resource] | None]
