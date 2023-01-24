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
    start: t.Optional[str]
    end: t.Optional[str]
    source: t.Optional[str]


class Graph(t.TypedDict):
    nodes: t.List[Node]
    edges: t.List[Edge]
    locutions: t.List[Locution]
