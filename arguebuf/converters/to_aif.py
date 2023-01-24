from __future__ import annotations


from arguebuf.models.edge import Edge
from arguebuf.models.graph import Graph
from arguebuf.models.node import NO_SCHEME_LABEL, AbstractNode, AtomNode, SchemeNode
from arguebuf.models.scheme import scheme2aif
from arguebuf.schemas import aif
from arguebuf.services import dt


def to_aif(obj: Graph) -> aif.Graph:
    """Export structure of Graph instance to AIF argument graph format."""
    return {
        "nodes": [node_to_aif(node) for node in obj.nodes.values()],
        "edges": [edge_to_aif(edge) for edge in obj.edges.values()],
        "locutions": [],
    }


def node_to_aif(obj: AbstractNode) -> aif.Node:
    if isinstance(obj, AtomNode):
        return atom_to_aif(obj)
    elif isinstance(obj, SchemeNode):
        return scheme_to_aif(obj)

    raise ValueError("Node type not supported.")


def scheme_to_aif(obj: SchemeNode) -> aif.Node:
    """Export SchemeNode object into AIF Node object."""

    return {
        "nodeID": obj.id,
        "timestamp": dt.to_format(obj.metadata.updated, aif.DATE_FORMAT),
        "text": obj.scheme.value if obj.scheme else NO_SCHEME_LABEL,
        "type": scheme2aif[type(obj.scheme)] if obj.scheme else "",
    }


def atom_to_aif(obj: AtomNode) -> aif.Node:
    """Export AtomNode object into AIF Node object."""
    return {
        "nodeID": obj.id,
        "timestamp": dt.to_format(obj.metadata.updated, aif.DATE_FORMAT),
        "text": obj.plain_text,
        "type": "I",
    }


def edge_to_aif(obj: Edge) -> aif.Edge:
    """Export Edge object into AIF Edge format."""
    return {
        "edgeID": str(obj.id),
        "fromID": str(obj.source.id),
        "toID": str(obj.target.id),
        "formEdgeID": None,
    }
