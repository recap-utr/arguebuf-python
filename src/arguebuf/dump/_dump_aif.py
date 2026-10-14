from arguebuf.dt import to_format
from arguebuf.model import AbstractNode, AtomNode, Edge, Graph, SchemeNode
from arguebuf.model.node import NO_SCHEME_LABEL
from arguebuf.model.scheme import scheme2aif, scheme2aif_default
from arguebuf.schemas import aif

__all__ = ("dump_aif", "dump_edge", "dump_node")


def dump_aif[T](obj: Graph[T]) -> aif.Graph:
    """Export structure of Graph instance to AIF argument graph format."""
    return {
        "nodes": [dump_node(node, timestamp=True) for node in obj.nodes.values()],
        "edges": [
            {**dump_edge(edge), "formEdgeID": None} for edge in obj.edges.values()
        ],
        "locutions": [],
    }


def dump_node(obj: AbstractNode, timestamp: bool) -> aif.Node:
    """Export an atom or scheme node to an AIF node, with or without timestamp."""
    node: aif.Node

    match obj:
        case AtomNode():
            node = {"nodeID": obj.id, "text": obj.plain_text, "type": "I"}
        case SchemeNode(scheme=None):
            node = {"nodeID": obj.id, "text": NO_SCHEME_LABEL, "type": ""}
        case SchemeNode(scheme=scheme) if scheme is not None:
            node = {
                "nodeID": obj.id,
                "text": scheme2aif_default[type(scheme)]
                if scheme is type(scheme).DEFAULT
                else scheme.value,
                "type": scheme2aif[type(scheme)],
            }
        case _:
            raise ValueError("Node type not supported.")

    if timestamp:
        node["timestamp"] = to_format(obj.metadata.updated, aif.DATE_FORMAT)

    return node


def dump_edge(obj: Edge) -> aif.Edge:
    """Export an edge to an AIF edge."""
    return {"edgeID": obj.id, "fromID": obj.source.id, "toID": obj.target.id}
