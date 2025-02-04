from arguebuf import dt
from arguebuf.model import AbstractNode, AtomNode, Edge, Graph, SchemeNode
from arguebuf.model.node import NO_SCHEME_LABEL
from arguebuf.model.scheme import scheme2aif
from arguebuf.schemas import aif as aif_schema

__all__ = ("dump_aif",)


def dump_aif(obj: Graph) -> aif_schema.Graph:
    """Export structure of Graph instance to AIF argument graph format."""
    return {
        "nodes": [_dump_node(node) for node in obj.nodes.values()],
        "edges": [_dump_edge(edge) for edge in obj.edges.values()],
        "locutions": [],
    }


def _dump_node(obj: AbstractNode) -> aif_schema.Node:
    if isinstance(obj, AtomNode):
        return _dump_atom(obj)
    elif isinstance(obj, SchemeNode):
        return _dump_scheme(obj)

    raise ValueError("Node type not supported.")


def _dump_scheme(obj: SchemeNode) -> aif_schema.Node:
    """Export SchemeNode object into AIF Node object."""

    return {
        "nodeID": obj.id,
        "timestamp": dt.to_format(obj.metadata.updated, aif_schema.DATE_FORMAT),
        "text": obj.scheme.value if obj.scheme else NO_SCHEME_LABEL,
        "type": scheme2aif[type(obj.scheme)] if obj.scheme else "",
    }


def _dump_atom(obj: AtomNode) -> aif_schema.Node:
    """Export AtomNode object into AIF Node object."""
    return {
        "nodeID": obj.id,
        "timestamp": dt.to_format(obj.metadata.updated, aif_schema.DATE_FORMAT),
        "text": obj.plain_text,
        "type": "I",
    }


def _dump_edge(obj: Edge) -> aif_schema.Edge:
    """Export Edge object into AIF Edge format."""
    return {
        "edgeID": str(obj.id),
        "fromID": str(obj.source.id),
        "toID": str(obj.target.id),
        "formEdgeID": None,
    }
