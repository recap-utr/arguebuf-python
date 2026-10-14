from collections.abc import Mapping

from arguebuf.model import Graph
from arguebuf.model.edge import Edge
from arguebuf.model.node import AbstractNode, AtomNode
from arguebuf.model.scheme import Attack, Support
from arguebuf.schemas import argdown

from ._config import Config

__all__ = ("load_argdown",)


def load_argdown[T = str](
    obj: argdown.Graph,
    name: str | None = None,
    config: Config[T] = Config(),
) -> Graph[T]:
    """Generate Graph structure from JSON Argdown argument graph file
    (reference: https://argdown.org/).
    """
    g = config.graph(name)

    # every argdown node is an atom node
    for argdown_node in obj["map"]["nodes"]:
        g.add_node(atom_from_argdown(argdown_node, config))

    # argdown edges connect atom nodes directly, so a scheme node is put in between
    for argdown_edge in obj["map"]["edges"]:
        if edge := edge_from_argdown(argdown_edge, g.nodes, config):
            scheme = (
                Attack.DEFAULT
                if argdown_edge["relationType"] in ("attack", "contradictory")
                else Support.DEFAULT
            )
            scheme_node = config.SchemeNodeClass(scheme)
            g.add_edge(config.EdgeClass(edge.source, scheme_node, id=edge.id))
            g.add_edge(config.EdgeClass(scheme_node, edge.target))

    return g


def edge_from_argdown[T](
    obj: argdown.Edge, nodes: Mapping[str, AbstractNode], config: Config[T]
) -> Edge | None:
    """Generate Edge object from Argdown JSON Edge format."""
    return config.edge(nodes, obj["from"], obj["to"], obj["id"])


def atom_from_argdown[T](obj: argdown.Node, config: Config[T]) -> AtomNode[T]:
    """Generate AtomNode object from Argdown JSON Node object."""
    return config.AtomNodeClass(config.parse(obj["labelText"]), id=obj["id"])
