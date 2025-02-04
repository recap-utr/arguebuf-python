from arguebuf.model import AbstractNode, AtomNode, Edge, Graph, SchemeNode
from arguebuf.model.node import NO_SCHEME_LABEL
from arguebuf.model.scheme import scheme2aif
from arguebuf.schemas import xaif as xaif_schema

__all__ = ("dump_xaif",)


def dump_xaif(obj: Graph) -> xaif_schema.Graph:
    """Export structure of Graph instance to AIF argument graph format."""
    return {
        "AIF": {
            "nodes": [_dump_node(node) for node in obj.nodes.values()],
            "edges": [_dump_edge(edge) for edge in obj.edges.values()],
            "locutions": [],
            "schemefulfillments": [],
            "participants": [],
        },
        "text": "<br>".join(resource.text for resource in obj.resources.values()),
        "OVA": {
            "firstname": "",
            "surname": "",
            "url": "",
            "nodes": [],
            "edges": [],
        },
    }


def _dump_node(obj: AbstractNode) -> xaif_schema.AifNode:
    if isinstance(obj, AtomNode):
        return _dump_atom(obj)
    elif isinstance(obj, SchemeNode):
        return _dump_scheme(obj)

    raise ValueError("Node type not supported.")


def _dump_scheme(obj: SchemeNode) -> xaif_schema.AifNode:
    """Export SchemeNode object into AIF Node object."""

    return {
        "nodeID": obj.id,
        "text": obj.scheme.value if obj.scheme else NO_SCHEME_LABEL,
        "type": scheme2aif[type(obj.scheme)] if obj.scheme else "",
    }


def _dump_atom(obj: AtomNode) -> xaif_schema.AifNode:
    """Export AtomNode object into AIF Node object."""
    return {
        "nodeID": obj.id,
        "text": obj.plain_text,
        "type": "I",
    }


def _dump_edge(obj: Edge) -> xaif_schema.AifEdge:
    """Export Edge object into AIF Edge format."""
    return {
        "edgeID": str(obj.id),
        "fromID": str(obj.source.id),
        "toID": str(obj.target.id),
    }
