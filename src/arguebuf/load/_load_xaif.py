from collections.abc import Mapping

from arguebuf.model import Graph
from arguebuf.model.edge import Edge
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.scheme import aif2scheme, resolve_aif_scheme
from arguebuf.schemas import xaif

from ._config import Config

__all__ = ("load_xaif",)


def load_xaif[T = str](
    obj: xaif.Graph, name: str | None = None, config: Config[T] = Config()
) -> Graph[T]:
    """Generate Graph structure from xAIF argument graph file."""
    g = config.graph(name)
    aif_graph = obj["AIF"]

    for aif_node in aif_graph["nodes"]:
        node = (
            atom_from_xaif(aif_node, config)
            if aif_node["type"] == "I"
            else scheme_from_xaif(aif_node, config)
        )

        if node:
            g.add_node(node)

    for aif_edge in aif_graph["edges"]:
        if edge := edge_from_xaif(aif_edge, g.nodes, config):
            g.add_edge(edge)

    return g


def scheme_from_xaif[T](obj: xaif.AifNode, config: Config[T]) -> SchemeNode | None:
    """Generate SchemeNode object from xAIF Node object."""
    if obj["type"] not in aif2scheme:
        return None

    return config.SchemeNodeClass(
        resolve_aif_scheme(obj["type"], obj.get("scheme", obj["text"])),
        id=obj["nodeID"],
    )


def atom_from_xaif[T](obj: xaif.AifNode, config: Config[T]) -> AtomNode[T]:
    """Generate AtomNode object from xAIF Node object."""
    return config.AtomNodeClass(config.parse(obj["text"]), id=obj["nodeID"])


def edge_from_xaif[T](
    obj: xaif.AifEdge, nodes: Mapping[str, AbstractNode], config: Config[T]
) -> Edge | None:
    """Generate Edge object from xAIF Edge format."""
    return config.edge(nodes, obj["fromID"], obj["toID"], str(obj["edgeID"]))
