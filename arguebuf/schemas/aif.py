import typing as t

SchemeType = t.Literal["RA", "CA", "MA", "PA", ""]
NodeType = t.Literal["RA", "CA", "MA", "PA", "", "I", "TA", "YA", "L"]
DATE_FORMAT = "YYYY-MM-DD HH:mm:ss"


class Node(t.TypedDict):
    nodeID: str
    text: str
    type: NodeType
    timestamp: str


class Edge(t.TypedDict):
    edgeID: str
    fromID: str
    toID: str
    formEdgeID: None


class Locution(t.TypedDict):
    nodeID: str
    personID: str
    timestamp: str
    start: str | None
    end: str | None
    source: str | None


class Graph(t.TypedDict):
    nodes: list[Node]
    edges: list[Edge]
    locutions: list[Locution]
