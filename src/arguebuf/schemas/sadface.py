import typing as t

from arguebuf.model.userdata import JsonObject

__all__ = (
    "Core",
    "Edge",
    "Graph",
    "Metadata",
    "Node",
    "NodeType",
    "Resource",
    "Source",
)

# `scheme` is the generic type of older versions, it is refined by its name
type NodeType = t.Literal["atom", "scheme", "inference", "conflict"]


class Source(t.TypedDict):
    resource_id: t.ReadOnly[str]
    text: t.ReadOnly[str]
    offset: t.NotRequired[t.ReadOnly[int]]
    length: t.NotRequired[t.ReadOnly[int]]


class Node(t.TypedDict):
    id: t.ReadOnly[str]
    type: t.ReadOnly[NodeType]
    text: t.NotRequired[t.ReadOnly[str]]
    name: t.NotRequired[t.ReadOnly[str]]
    sources: t.NotRequired[t.ReadOnly[list[Source]]]
    metadata: t.NotRequired[t.ReadOnly[JsonObject]]


class Edge(t.TypedDict):
    id: t.ReadOnly[str]
    source_id: t.ReadOnly[str]
    target_id: t.ReadOnly[str]


class Resource(t.TypedDict):
    id: t.ReadOnly[str]
    content: t.NotRequired[t.ReadOnly[str]]
    type: t.NotRequired[t.ReadOnly[str]]
    metadata: t.NotRequired[t.ReadOnly[JsonObject]]


class Core(t.TypedDict):
    id: t.ReadOnly[str]
    version: t.ReadOnly[str]
    analyst_email: t.NotRequired[t.ReadOnly[str]]
    analyst_name: t.NotRequired[t.ReadOnly[str]]
    created: t.NotRequired[t.ReadOnly[str]]
    edited: t.NotRequired[t.ReadOnly[str]]
    description: t.NotRequired[t.ReadOnly[str]]
    notes: t.NotRequired[t.ReadOnly[str]]
    title: t.NotRequired[t.ReadOnly[str]]


class Metadata(t.TypedDict):
    core: t.ReadOnly[Core]


class Graph(t.TypedDict):
    nodes: t.ReadOnly[list[Node]]
    edges: t.ReadOnly[list[Edge]]
    metadata: t.ReadOnly[Metadata]
    resources: t.NotRequired[t.ReadOnly[list[Resource]]]
