import typing as t

NodeType = t.Literal["scheme", "atom"]
DATE_FORMAT = "YYYY-MM-DDTHH:mm:ss"


class Node(t.TypedDict):
    id: str
    text: str
    type: NodeType
    name: str
    sources: list[str]
    metadata: dict[str, t.Any]


class Edge(t.TypedDict):
    id: str
    source_id: str
    target_id: str


class Core(t.TypedDict):
    analyst_email: str
    analyst_name: str
    created: str
    description: str
    edited: str
    id: str
    notes: str
    title: str
    version: str


class Metadata(t.TypedDict):
    core: Core


class Graph(t.TypedDict):
    nodes: list[Node]
    edges: list[Edge]
    metadata: Metadata
