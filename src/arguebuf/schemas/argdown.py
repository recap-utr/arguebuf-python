import typing as t


class Node(t.TypedDict):
    id: str
    title: str  # title of argument/statement
    type: str  # check if "argument-map-node", or "statement-map-node"
    labelTitle: str  # title of argument/statement
    labelText: str  # text of argument/statement


# `from` is a keyword and thus requires the functional syntax
Edge = t.TypedDict(
    "Edge",
    {"id": str, "type": str, "relationType": str, "from": str, "to": str},
)


class Map(t.TypedDict):
    nodes: list[Node]
    edges: list[Edge]


class Graph(t.TypedDict):
    map: Map
