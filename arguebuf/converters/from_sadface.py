from __future__ import annotations

import typing as t

import pendulum

from arguebuf.converters.config import ConverterConfig, DefaultConverter
from arguebuf.models.edge import Edge, warn_missing_nodes
from arguebuf.models.graph import Graph
from arguebuf.models.node import (
    AbstractNode,
    AtomNode,
    Attack,
    Preference,
    Rephrase,
    SchemeNode,
    Support,
)
from arguebuf.schemas import sadface
from arguebuf.services import dt, utils


def from_sadface(
    obj: sadface.Graph,
    name: t.Optional[str] = None,
    config: ConverterConfig = DefaultConverter,
) -> Graph:
    """Generate Graph structure from SADFace argument graph file
    (reference: https://github.com/Open-Argumentation/SADFace/blob/master/examples/hangback/data.json).
    """
    g = config.GraphClass(name)

    for sadface_node in obj["nodes"]:
        node = (
            atom_from_sadface(sadface_node, config)
            if sadface_node["type"] == "atom"
            else scheme_from_sadface(sadface_node, config)
        )

        if node:
            g.add_node(node)

    for sadface_edge in obj["edges"]:
        if edge := edge_from_sadface(sadface_edge, g.nodes, config):
            g.add_edge(edge)

    # create
    # object
    created = dt.from_format(obj["metadata"]["core"]["created"], sadface.DATE_FORMAT)
    updated = dt.from_format(obj["metadata"]["core"]["edited"], sadface.DATE_FORMAT)
    metadata = config.MetadataClass(created, updated)
    g.metadata = metadata

    # create Analyst object
    analyst = config.AnalystClass(
        name=obj["metadata"]["core"]["analyst_name"],
        email=obj["metadata"]["core"]["analyst_email"],
    )
    g.add_analyst(analyst)

    # create Userdata dict
    g.userdata = {
        "notes": obj["metadata"]["core"]["notes"],
        "description": obj["metadata"]["core"]["description"],
        "title": obj["metadata"]["core"]["title"],
        "sadfaceVersion": obj["metadata"]["core"]["version"],
    }

    return g


def atom_from_sadface(obj: sadface.Node, config: ConverterConfig) -> AtomNode:
    """Generate AtomNode object from SADFace Node object."""
    timestamp = pendulum.now()
    return config.AtomNodeClass(
        id=obj["id"],
        text=utils.parse(obj["text"], config.nlp),
        userdata=obj["metadata"],
        metadata=config.MetadataClass(timestamp, timestamp),
    )


def scheme_from_sadface(obj: sadface.Node, config: ConverterConfig) -> SchemeNode:
    """Generate SchemeNode object from SADFace Node object."""
    name = None

    if obj["name"] == "support":
        name = Support.DEFAULT
    elif obj["name"] == "attack":
        name = Attack.DEFAULT
    elif obj["name"] == "rephrase":
        name = Rephrase.DEFAULT
    elif obj["name"] == "preference":
        name = Preference.DEFAULT

    timestamp = pendulum.now()

    return config.SchemeNodeClass(
        id=obj["id"],
        userdata=obj["metadata"],
        metadata=config.MetadataClass(timestamp, timestamp),
        scheme=name,
    )


def edge_from_sadface(
    obj: sadface.Edge, nodes: t.Mapping[str, AbstractNode], config: ConverterConfig
) -> t.Optional[Edge]:
    """Generate Edge object from SADFace Edge format."""
    source_id = obj.get("source_id")
    target_id = obj.get("target_id")

    if source_id in nodes and target_id in nodes:
        return config.EdgeClass(
            id=obj["id"],
            source=nodes[source_id],
            target=nodes[target_id],
        )
    else:
        warn_missing_nodes(obj["id"], source_id, target_id)

    return None
