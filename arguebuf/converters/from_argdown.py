import typing as t

import pendulum

from arguebuf.converters.config import ConverterConfig, DefaultConverter
from arguebuf.models.edge import Edge, warn_missing_nodes
from arguebuf.models.graph import Graph
from arguebuf.models.metadata import Metadata
from arguebuf.models.node import AbstractNode, Attack, Support
from arguebuf.schemas import argdown


def from_argdown(
    obj: argdown.Graph,
    name: t.Optional[str] = None,
    config: ConverterConfig = DefaultConverter,
) -> Graph:
    """Generate Graph structure from JSON Argdown argument graph file
    (reference: https://argdown.org/).
    """
    g = config.GraphClass(name)

    timestamp = pendulum.now()

    # Every node in obj["nodes"] is a atom node
    for argdown_node in obj["map"]["nodes"]:
        node = config.AtomNodeClass.from_argdown_json(argdown_node, config.nlp)

        if node:
            g.add_node(node)

    for argdown_edge in obj["map"]["edges"]:
        if edge := edge_from_argdown(argdown_edge, g.nodes, config.EdgeClass):
            g.add_edge(edge)
            if argdown_edge["relationType"] == "support":
                scheme = Support.DEFAULT
            elif argdown_edge["relationType"] == "attack":
                scheme = Attack.DEFAULT
            elif argdown_edge["relationType"] == "contradictory":
                scheme = Attack.DEFAULT
            elif argdown_edge["relationType"] == "undercut":
                scheme = Support.DEFAULT
            else:
                scheme = Support.DEFAULT
            # create scheme_node for edge
            scheme_node = config.SchemeNodeClass(
                metadata=Metadata(timestamp, timestamp),
                scheme=scheme,
            )
            g.add_node(scheme_node)

            # create edge from source to scheme_node and an edge from scheme_node to target
            g.add_edge(Edge(edge.source, scheme_node))
            g.add_edge(Edge(scheme_node, edge.target))

    metadata = Metadata(timestamp, timestamp)
    g.metadata = metadata

    return g


def edge_from_argdown(
    obj: argdown.Edge,
    nodes: t.Mapping[str, AbstractNode],
    edge_class: t.Type[Edge] = Edge,
) -> t.Optional[Edge]:
    """Generate Edge object from Argdown JSON Edge format."""
    if "from" in obj:
        source_id = obj["from"]  # type: ignore
    else:
        source_id = obj["source"]

    if "to" in obj:
        target_id = obj["to"]  # type: ignore
    else:
        target_id = obj["target"]

    edge_id = obj["id"]

    if source_id in nodes and target_id in nodes:
        return edge_class(
            id=edge_id,
            source=nodes[source_id],
            target=nodes[target_id],
        )
    else:
        warn_missing_nodes(edge_id, source_id, target_id)

    return None
