from arguebuf._dt import to_format
from arguebuf.model import AbstractNode, AtomNode, Edge, GraphView, SchemeNode
from arguebuf.model.node import NO_SCHEME_LABEL
from arguebuf.model.scheme import (
    SCHEME_AIF_DEFAULTS,
    SCHEME_AIF_TYPES,
    is_default_scheme,
)
from arguebuf.schemas import aif

__all__ = ("dump_aif", "dump_edge", "dump_node")


def dump_aif[A, S, E, R, P, N, G](graph: GraphView[A, S, E, R, P, N, G]) -> aif.Graph:
    """Export structure of Graph instance to AIF argument graph format."""
    return {
        "nodes": [dump_node(node, timestamp=True) for node in graph.nodes.values()],
        "edges": [
            {**dump_edge(edge), "formEdgeID": None} for edge in graph.edges.values()
        ],
        "locutions": [],
    }


def dump_node(obj: AbstractNode, *, timestamp: bool) -> aif.Node:
    """Export an atom or scheme node to an AIF node, with or without timestamp."""
    node: aif.Node

    match obj:
        case AtomNode():
            node = {"nodeID": obj.id, "text": obj.text, "type": "I"}
        case SchemeNode(scheme=None):
            node = {"nodeID": obj.id, "text": NO_SCHEME_LABEL, "type": ""}
        case SchemeNode(scheme=scheme) if scheme is not None:
            node = {
                "nodeID": obj.id,
                "text": SCHEME_AIF_DEFAULTS[type(scheme)]
                if is_default_scheme(scheme)
                else scheme.value,
                "type": SCHEME_AIF_TYPES[type(scheme)],
            }
        case _:
            raise ValueError("Node type not supported.")

    if timestamp:
        node["timestamp"] = to_format(obj.metadata.updated, aif.DATE_FORMAT)

    return node


def dump_edge[E](obj: Edge[E]) -> aif.Edge:
    """Export an edge to an AIF edge."""
    return {"edgeID": obj.id, "fromID": obj.source, "toID": obj.target}
