import typing as t
import arguebuf as ag

NodeType = t.Literal["scheme", "atom"]
DATE_FORMAT = "YYYY-MM-DDTHH:mm:ss"


class Node(t.TypedDict):
    id: str
    text: str
    type: NodeType
    name: str
    sources: list
    metadata: t.Dict[str, t.Any]


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
    nodes: t.List[Node]
    edges: t.List[Edge]
    metadata: Metadata
