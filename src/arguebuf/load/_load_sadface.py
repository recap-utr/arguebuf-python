from collections.abc import Mapping

from arguebuf.dt import from_isoformat
from arguebuf.model import Graph
from arguebuf.model.analyst import Analyst
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.reference import Reference
from arguebuf.model.resource import AbstractResource, Resource
from arguebuf.model.scheme import (
    Attack,
    Preference,
    Rephrase,
    Scheme,
    Support,
    normalize_scheme_label,
    resolve_scheme,
)
from arguebuf.model.userdata import DEFAULT_CODECS, Codec, Codecs, JsonObject
from arguebuf.schemas import sadface

from ._helpers import add_edge, compact, log, new_reference

__all__ = ("load_sadface",)

# normalized names of generic `scheme` nodes that denote a scheme type instead of a specific scheme
name2scheme_type: dict[str, type[Scheme]] = {
    "support": Support,
    "inference": Support,
    "attack": Attack,
    "conflict": Attack,
    "rephrase": Rephrase,
    "preference": Preference,
}


def load_sadface[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
](
    obj: sadface.Graph,
    name: str | None = None,
    *,
    codecs: Codecs[A, S, E, G, R, P, N] = DEFAULT_CODECS,
) -> Graph[A, S, E, G, R, P, N]:
    """Generate Graph structure from SADFace argument graph file.

    Reference: https://github.com/Open-Argumentation/SADFace/blob/master/examples/hangback/data.json
    The first source of an atom becomes its reference.
    The timestamps are ISO 8601, a missing creation date falls back to the edit date.
    Nodes of unknown types are skipped with a warning.
    """
    core = obj["metadata"]["core"]
    edited = from_isoformat(core.get("edited"))
    g: Graph[A, S, E, G, R, P, N] = Graph(
        name,
        metadata=Metadata(from_isoformat(core.get("created")) or edited, edited),
        userdata=codecs.graph.validate_python(
            compact(
                {
                    "notes": core.get("notes"),
                    "description": core.get("description"),
                    "title": core.get("title"),
                    "sadfaceVersion": core.get("version"),
                }
            )
        ),
    )

    if core.get("analyst_name") or core.get("analyst_email"):
        g.add_analyst(
            Analyst(
                core.get("analyst_name") or None,
                email=core.get("analyst_email") or None,
                userdata=codecs.analyst.validate_python({}),
            )
        )

    for sadface_resource in obj.get("resources") or []:
        g.add_resource(
            Resource(
                sadface_resource.get("content") or "",
                userdata=codecs.resource.validate_python(
                    sadface_resource.get("metadata") or {}
                ),
                id=sadface_resource["id"],
            )
        )

    for sadface_node in obj["nodes"]:
        match sadface_node["type"]:
            case "atom":
                g.add_node(atom_from_sadface(sadface_node, g.resources, codecs.atom))
            case "scheme" | "inference" | "conflict":
                g.add_node(scheme_from_sadface(sadface_node, codecs.scheme))
            case node_type:
                log.warning(
                    "Skipping node '%s' of unknown type '%s'.",
                    sadface_node["id"],
                    node_type,
                )

    for edge in obj["edges"]:
        add_edge(g, codecs, edge["source_id"], edge["target_id"], edge["id"])

    return g


def atom_from_sadface[A](
    obj: sadface.Node, resources: Mapping[str, AbstractResource], codec: Codec[A]
) -> AtomNode[A]:
    """Generate AtomNode object from SADFace Node object."""
    reference: Reference | None = None

    if sources := obj.get("sources"):
        source = sources[0]
        reference = new_reference(
            source["text"],
            source["resource_id"],
            source.get("offset"),
            resources,
            f"atom node '{obj['id']}'",
        )

    return AtomNode(
        obj.get("text", ""),
        reference=reference,
        userdata=codec.validate_python(obj.get("metadata") or {}),
        id=obj["id"],
    )


def scheme_from_sadface[S](obj: sadface.Node, codec: Codec[S]) -> SchemeNode[S]:
    """Generate SchemeNode object from SADFace Node object.

    `inference` nodes are resolved by their name, `conflict` nodes are attacks.
    Generic `scheme` nodes are resolved via `name2scheme_type` or as inference names,
    a missing name yields no scheme.
    """
    name = obj.get("name") or ""
    scheme: Scheme | None

    match obj["type"]:
        case "inference":
            scheme = resolve_scheme(Support, name)
        case "conflict":
            scheme = Attack.DEFAULT
        case _ if scheme_type := name2scheme_type.get(normalize_scheme_label(name)):
            scheme = scheme_type.DEFAULT
        case _:
            scheme = resolve_scheme(Support, name) if name else None

    return SchemeNode(
        scheme,
        userdata=codec.validate_python(obj.get("metadata") or {}),
        id=obj["id"],
    )
