from collections.abc import Mapping

from arguebuf.dt import from_isoformat, now
from arguebuf.model import Graph
from arguebuf.model.edge import Edge
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.scheme import Attack, Preference, Rephrase, Scheme, Support
from arguebuf.schemas import sadface

from ._config import Config

__all__ = ("load_sadface",)

name2scheme: dict[str, Scheme] = {
    "support": Support.DEFAULT,
    "attack": Attack.DEFAULT,
    "rephrase": Rephrase.DEFAULT,
    "preference": Preference.DEFAULT,
}


def load_sadface[T = str](
    obj: sadface.Graph,
    name: str | None = None,
    config: Config[T] = Config(),
) -> Graph[T]:
    """Generate Graph structure from SADFace argument graph file
    (reference: https://github.com/Open-Argumentation/SADFace/blob/master/examples/hangback/data.json).
    """
    core = obj["metadata"]["core"]
    g = config.graph(name)
    g.metadata = config.MetadataClass(
        from_isoformat(core["created"]) or now(),
        from_isoformat(core["edited"]) or now(),
    )
    g.userdata = {
        "notes": core["notes"],
        "description": core["description"],
        "title": core["title"],
        "sadfaceVersion": core["version"],
    }
    g.add_analyst(
        config.AnalystClass(core["analyst_name"], email=core["analyst_email"])
    )

    for sadface_node in obj["nodes"]:
        g.add_node(
            atom_from_sadface(sadface_node, config)
            if sadface_node["type"] == "atom"
            else scheme_from_sadface(sadface_node, config)
        )

    for sadface_edge in obj["edges"]:
        if edge := edge_from_sadface(sadface_edge, g.nodes, config):
            g.add_edge(edge)

    return g


def atom_from_sadface[T](obj: sadface.Node, config: Config[T]) -> AtomNode[T]:
    """Generate AtomNode object from SADFace Node object."""
    return config.AtomNodeClass(
        config.parse(obj["text"]),
        userdata=obj["metadata"],
        id=obj["id"],
    )


def scheme_from_sadface[T](obj: sadface.Node, config: Config[T]) -> SchemeNode:
    """Generate SchemeNode object from SADFace Node object."""
    return config.SchemeNodeClass(
        name2scheme.get(obj["name"]),
        userdata=obj["metadata"],
        id=obj["id"],
    )


def edge_from_sadface[T](
    obj: sadface.Edge, nodes: Mapping[str, AbstractNode], config: Config[T]
) -> Edge | None:
    """Generate Edge object from SADFace Edge format."""
    return config.edge(nodes, obj["source_id"], obj["target_id"], obj["id"])
