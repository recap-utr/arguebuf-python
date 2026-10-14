from arguebuf.model import Graph
from arguebuf.schemas import xaif

from ._dump_aif import dump_edge, dump_node

__all__ = ("dump_xaif",)


def dump_xaif[T](obj: Graph[T]) -> xaif.Graph:
    """Export structure of Graph instance to xAIF argument graph format.

    xAIF nodes have no timestamps, so they are omitted.
    """
    return {
        "AIF": {
            "nodes": [dump_node(node, timestamp=False) for node in obj.nodes.values()],
            "edges": [dump_edge(edge) for edge in obj.edges.values()],
            "locutions": [],
            "schemefulfillments": [],
            "descriptorfulfillments": [],
            "participants": [],
        },
        "text": "<br>".join(resource.plain_text for resource in obj.resources.values()),
        "dialog": False,
    }
