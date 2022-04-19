import typing as t


class Node(t.TypedDict):
    nodeID: str
    text: str
    type: str
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


# SchemeType = t.Union["RA", "CA", "MA", "TA", "PA", "YA"];

DATE_FORMAT = "yyyy-MM-dd HH:mm:ss"
