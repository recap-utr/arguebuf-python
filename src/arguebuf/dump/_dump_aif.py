from arguebuf._dt import to_format
from arguebuf.model import AbstractNode, AtomNode, Edge, GraphView, SchemeNode
from arguebuf.model.scheme import (
    SCHEME_AIF_DEFAULTS,
    SCHEME_AIF_TYPES,
    Support,
    is_default_scheme,
)
from arguebuf.schemas import aif

__all__ = ("dump_aif", "dump_edge", "dump_node")


def dump_aif[A, S, E, R, P, N, G](graph: GraphView[A, S, E, R, P, N, G]) -> aif.Graph:
    """Export structure of Graph instance to AIF argument graph format."""
    # unlike xAIF, AIF lists timestamps and a `formEdgeID`
    return {
        "nodes": [
            {
                **dump_node(node),
                "timestamp": to_format(node.metadata.created, aif.DATE_FORMAT),
            }
            for node in graph.nodes.values()
        ],
        "edges": [
            {**dump_edge(edge), "formEdgeID": None} for edge in graph.edges.values()
        ],
        "locutions": [],
    }


def dump_node(obj: AbstractNode) -> aif.Node:
    """Export an atom or scheme node to an AIF node without timestamp."""
    match obj:
        case AtomNode():
            text, node_type = obj.text, "I"
        # AIF has no untyped schemes, so they are exported as default inferences like in AIFdb
        case SchemeNode(scheme=None):
            text, node_type = SCHEME_AIF_DEFAULTS[Support], SCHEME_AIF_TYPES[Support]
        case SchemeNode(scheme=scheme) if scheme is not None:
            text = (
                SCHEME_AIF_DEFAULTS[type(scheme)]
                if is_default_scheme(scheme)
                else scheme.value
            )
            node_type = SCHEME_AIF_TYPES[type(scheme)]
        case _:
            raise ValueError("Node type not supported.")

    return {"nodeID": obj.id, "text": text, "type": node_type}


def dump_edge[E](obj: Edge[E]) -> aif.Edge:
    """Export an edge to an AIF edge without `formEdgeID`."""
    return {"edgeID": obj.id, "fromID": obj.source, "toID": obj.target}
