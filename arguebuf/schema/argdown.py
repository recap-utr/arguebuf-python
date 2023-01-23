import typing as t


class Node(t.TypedDict):
    id: str
    title: str  # title of argument/statement
    type: str  # check if "argument-map-node", or "statment-map-node"
    labelTitle: str  # title of argument/statement
    labelText: str  # text of argument/statement


class Edge(t.TypedDict):
    id: str
    type: str
    relationType: str
    source: str
    target: str


class Map(t.TypedDict):
    nodes: t.List[Node]
    edges: t.List[Edge]


class Graph(t.TypedDict):
    map: Map
