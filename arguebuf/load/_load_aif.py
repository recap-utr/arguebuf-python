import typing as t

import pendulum

from arguebuf import dt
from arguebuf.model import Graph, utils
from arguebuf.model.edge import Edge, warn_missing_nodes
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.scheme import aif2scheme, text2scheme
from arguebuf.schemas import aif

from ._config import Config, DefaultConfig

__all__ = ("load_aif",)


def load_aif(
    obj: aif.Graph,
    name: t.Optional[str] = None,
    config: Config = DefaultConfig,
) -> Graph:
    """Generate Graph structure from AIF argument graph file
    (reference: http://www.wi2.uni-trier.de/shared/publications/2019_LenzOllingerSahitajBergmann_ICCBR.pdf)

    """
    g = config.GraphClass(name)

    for aif_node in obj["nodes"]:
        node = (
            atom_from_aif(aif_node, config)
            if aif_node["type"] == "I"
            else scheme_from_aif(aif_node, config)
        )

        if node:
            g.add_node(node)

    for aif_edge in obj["edges"]:
        if edge := edge_from_aif(aif_edge, g.nodes, config):
            g.add_edge(edge)

    return g


def atom_from_aif(obj: aif.Node, config: Config) -> AtomNode:
    """Generate AtomNode object from AIF Node object."""
    timestamp = dt.from_format(obj.get("timestamp"), aif.DATE_FORMAT) or pendulum.now()

    return config.AtomNodeClass(
        id=obj["nodeID"],
        metadata=config.MetadataClass(timestamp, timestamp),
        text=utils.parse(obj["text"], config.nlp),
    )


def scheme_from_aif(obj: aif.Node, config: Config) -> t.Optional[SchemeNode]:
    """Generate SchemeNode object from AIF Node object."""

    aif_type = obj["type"]
    aif_scheme: str = obj.get("scheme", obj["text"])

    if aif_type in aif2scheme:
        scheme = aif2scheme[t.cast(aif.SchemeType, aif_type)]

        # TODO: Handle formatting like capitalization, spaces, underscores, etc.
        # TODO: Araucaria does not use spaces between scheme names
        # aif_scheme = re.sub("([A-Z])", r" \1", aif_scheme)
        if scheme and (found_scheme := text2scheme[type(scheme)].get(aif_scheme)):
            scheme = found_scheme

        timestamp = (
            dt.from_format(obj.get("timestamp"), aif.DATE_FORMAT) or pendulum.now()
        )

        return config.SchemeNodeClass(
            id=obj["nodeID"],
            metadata=config.MetadataClass(timestamp, timestamp),
            scheme=scheme,
        )

    return None


def edge_from_aif(
    obj: aif.Edge, nodes: t.Mapping[str, AbstractNode], config: Config
) -> t.Optional[Edge]:
    """Generate Edge object from AIF Edge format."""
    source_id = obj.get("fromID")
    target_id = obj.get("toID")

    if source_id in nodes and target_id in nodes:
        return config.EdgeClass(
            id=obj["edgeID"],
            source=nodes[source_id],
            target=nodes[target_id],
        )
    else:
        warn_missing_nodes(obj["edgeID"], source_id, target_id)

    return None
