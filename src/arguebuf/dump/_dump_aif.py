from arguebuf.dt import to_format
from arguebuf.model import AbstractNode, AtomNode, Edge, Graph, SchemeNode
from arguebuf.model.node import NO_SCHEME_LABEL
from arguebuf.model.scheme import scheme2aif
from arguebuf.schemas import aif as aif_schema

__all__ = ("dump_aif",)


def dump_aif[T](obj: Graph[T]) -> aif_schema.Graph:
    """Export structure of Graph instance to AIF argument graph format."""
    return {
        "nodes": [_dump_node(node) for node in obj.nodes.values()],
        "edges": [_dump_edge(edge) for edge in obj.edges.values()],
        "locutions": [],
    }


def _dump_node(obj: AbstractNode) -> aif_schema.Node:
    timestamp = to_format(obj.metadata.updated, aif_schema.DATE_FORMAT)

    match obj:
        case AtomNode():
            return _dump_atom(obj, timestamp)
        case SchemeNode():
            return _dump_scheme(obj, timestamp)
        case _:
            raise ValueError("Node type not supported.")


def _dump_scheme(obj: SchemeNode, timestamp: str) -> aif_schema.Node:
    return {
        "nodeID": obj.id,
        "timestamp": timestamp,
        "text": obj.scheme.value if obj.scheme else NO_SCHEME_LABEL,
        "type": scheme2aif[type(obj.scheme)] if obj.scheme else "",
    }


def _dump_atom[T](obj: AtomNode[T], timestamp: str) -> aif_schema.Node:
    return {
        "nodeID": obj.id,
        "timestamp": timestamp,
        "text": obj.plain_text,
        "type": "I",
    }


def _dump_edge(obj: Edge) -> aif_schema.Edge:
    return {
        "edgeID": obj.id,
        "fromID": obj.source.id,
        "toID": obj.target.id,
        "formEdgeID": None,
    }
