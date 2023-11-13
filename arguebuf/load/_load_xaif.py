import typing as t

import pendulum

from arguebuf.model import Graph, utils
from arguebuf.model.edge import Edge, warn_missing_nodes
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.scheme import aif2scheme, text2scheme
from arguebuf.schemas import xaif
from arguebuf.schemas.aif import SchemeType

from ._config import Config, DefaultConfig

__all__ = ("load_xaif",)


def load_xaif(
    obj: xaif.Graph, name: t.Optional[str] = None, config: Config = DefaultConfig
) -> Graph:
    """
    Generate Graph structure from xAif argument graph file
    """
    g = config.GraphClass(name)
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


def scheme_from_xaif(obj: xaif.AifNode, config: Config) -> t.Optional[SchemeNode]:
    """Generate SchemeNode object from xAif Node object."""

    aif_type = obj["type"]
    aif_scheme: str = obj.get("scheme", obj["text"])

    if aif_type in aif2scheme:
        scheme = aif2scheme[t.cast(SchemeType, aif_type)]

        # TODO: Handle formatting like capitalization, spaces, underscores, etc.
        # TODO: Araucaria does not use spaces between scheme names
        # aif_scheme = re.sub("([A-Z])", r" \1", aif_scheme)
        if scheme and (found_scheme := text2scheme[type(scheme)].get(aif_scheme)):
            scheme = found_scheme

        timestamp = pendulum.now()

        return config.SchemeNodeClass(
            id=obj["nodeID"],
            metadata=config.MetadataClass(timestamp, timestamp),
            scheme=scheme,
        )

    return None


def atom_from_xaif(obj: xaif.AifNode, config: Config) -> AtomNode:
    """Generate AtomNode object from xAif Node object."""
    timestamp = pendulum.now()

    return config.AtomNodeClass(
        id=obj["nodeID"],
        metadata=config.MetadataClass(timestamp, timestamp),
        text=utils.parse(obj["text"], config.nlp),
    )


def edge_from_xaif(
    obj: xaif.AifEdge, nodes: t.Mapping[str, AbstractNode], config: Config
) -> t.Optional[Edge]:
    """Generate Edge object from xAif Edge format."""
    source_id = obj.get("fromID")
    target_id = obj.get("toID")

    if source_id in nodes and target_id in nodes:
        return config.EdgeClass(
            id=str(obj["edgeID"]),
            source=nodes[source_id],
            target=nodes[target_id],
        )
    else:
        warn_missing_nodes(str(obj["edgeID"]), source_id, target_id)

    return None
