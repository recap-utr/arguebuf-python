from collections.abc import Mapping
from types import MappingProxyType
from typing import IO, Final, cast
from xml.etree import ElementTree as Tree

from arguebuf.model import Graph, GraphDraft
from arguebuf.model.issue import Reporter
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.scheme import Attack, Scheme, Support
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject
from arguebuf.schemas.microtexts import EdgeType

from ._helpers import Context, add_edge, connect, lookup

__all__ = ("load_microtexts",)

_EDGE_SCHEMES: Final[Mapping[EdgeType, Scheme]] = MappingProxyType(
    {
        "sup": Support.DEFAULT,
        "exa": Support.EXAMPLE,
        "reb": Attack.DEFAULT,
        "und": Attack.DEFAULT,
    }
)


def load_microtexts[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    obj: IO[str],
    *,
    name: str | None = None,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, R, P, N, G]:
    """Generate Graph structure from a microtexts (arggraph) XML file.

    ADUs become atoms with the text of their segment, joints concatenate their EDUs with spaces.
    Support (sup, exa) and attack (reb, und) edges become scheme nodes with the edge id,
    undercutters (und) target the scheme node of another edge,
    and additional sources (add) are linked to the scheme node of their target edge
    by an edge with their own id.
    The single atom without outgoing edges is the major claim.
    """
    root = Tree.parse(obj).getroot()
    ctx = Context(codecs, on_issue, strict)
    g: GraphDraft[A, S, E, R, P, N, G] = GraphDraft(
        name or root.get("id"),
        userdata=codecs.graph.validate_python(
            {"stance": root.get("stance"), "topic": root.get("topic_id")}
        ),
    )
    edges: list[tuple[str, str, str, EdgeType]] = [
        (
            elem.get("id", ""),
            elem.get("src", ""),
            elem.get("trg", ""),
            cast(EdgeType, elem.get("type")),
        )
        for elem in root.iter("edge")
    ]
    texts = {edu.get("id", ""): edu.text or "" for edu in root.iter("edu")}
    # dict as an ordered set for fast membership tests
    segments = dict.fromkeys(
        (source, target) for _, source, target, type in edges if type == "seg"
    )

    for joint in root.iter("joint"):
        joint_id = joint.get("id", "")
        # EDUs keep their document order
        texts[joint_id] = " ".join(
            text for edu_id, text in texts.items() if (edu_id, joint_id) in segments
        )

    adu2segment = {target: source for source, target in segments}

    for adu in root.iter("adu"):
        adu_id = adu.get("id", "")

        if (
            text := lookup(
                ctx, texts, adu2segment.get(adu_id), "segment", f"adu '{adu_id}'"
            )
        ) is None:
            continue

        g.add_node(
            AtomNode(
                text,
                userdata=codecs.atom.validate_python({"type": adu.get("type")}),
                id=adu_id,
            )
        )

    # all scheme nodes are added first since undercutters may target later edges
    for id, _, _, type in edges:
        if (scheme := _EDGE_SCHEMES.get(type)) is not None:
            g.add_node(
                SchemeNode(
                    scheme,
                    userdata=codecs.scheme.validate_python({}),
                    id=id,
                )
            )

    schemes = g.scheme_nodes

    for id, source, target, type in edges:
        if id in schemes:
            connect(g, ctx, [source], id, target)
        elif type == "add":
            add_edge(g, ctx, source, target, id)

    g.major_claim = g.root_node

    return g.freeze()
