from arguebuf.model import AbstractNode, AtomNode, Edge, Graph, SchemeNode
from arguebuf.model.node import NO_SCHEME_LABEL
from arguebuf.model.scheme import scheme2aif
from arguebuf.schemas import xaif as xaif_schema

__all__ = ("dump_xaif",)


def dump_xaif[T](obj: Graph[T]) -> xaif_schema.Graph:
    """Export structure of Graph instance to xAIF argument graph format."""
    return {
        "AIF": {
            "nodes": [_dump_node(node) for node in obj.nodes.values()],
            "edges": [_dump_edge(edge) for edge in obj.edges.values()],
            "locutions": [],
            "schemefulfillments": [],
            "participants": [],
        },
        "text": "<br>".join(resource.plain_text for resource in obj.resources.values()),
        "OVA": {
            "firstname": "",
            "surname": "",
            "url": "",
            "nodes": [],
            "edges": [],
        },
    }


def _dump_node(obj: AbstractNode) -> xaif_schema.AifNode:
    match obj:
        case AtomNode():
            return _dump_atom(obj)
        case SchemeNode():
            return _dump_scheme(obj)
        case _:
            raise ValueError("Node type not supported.")


def _dump_scheme(obj: SchemeNode) -> xaif_schema.AifNode:
    return {
        "nodeID": obj.id,
        "text": obj.scheme.value if obj.scheme else NO_SCHEME_LABEL,
        "type": scheme2aif[type(obj.scheme)] if obj.scheme else "",
    }


def _dump_atom[T](obj: AtomNode[T]) -> xaif_schema.AifNode:
    return {
        "nodeID": obj.id,
        "text": obj.plain_text,
        "type": "I",
    }


def _dump_edge(obj: Edge) -> xaif_schema.AifEdge:
    return {
        "edgeID": obj.id,
        "fromID": obj.source.id,
        "toID": obj.target.id,
    }
