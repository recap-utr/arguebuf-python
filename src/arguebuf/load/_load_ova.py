import dataclasses

from arguebuf.dt import from_format
from arguebuf.model import Graph, GraphDraft
from arguebuf.model.analyst import Analyst
from arguebuf.model.issue import Reporter
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.reference import Reference
from arguebuf.model.resource import Resource
from arguebuf.model.scheme import aif2scheme, resolve_aif_scheme
from arguebuf.model.userdata import DEFAULT_CODECS, Codec, Codecs, JsonObject
from arguebuf.model.utils import uuid
from arguebuf.schemas import aif, ova

from ._helpers import (
    Context,
    add_edge,
    add_node,
    lookup,
    new_participant,
    relocate,
    stringify_id,
)
from ._html import parse_html

__all__ = ("load_ova",)


def load_ova[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    obj: ova.Graph,
    *,
    name: str | None = None,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, R, P, N, G]:
    """Generate Graph structure from OVA argument graph file.

    Reference: http://ova.uni-trier.de/
    The resource text is the plain text of the highlighted `txt` (see `parse_html`),
    falling back to `plain_txt`.
    Spans with the id `node<atom id>` become references with offsets into it.
    Dialog nodes (L, TA, YA) and their edges are skipped.
    Numeric ids are converted to strings.
    """
    g: GraphDraft[A, S, E, R, P, N, G] = GraphDraft(
        name, userdata=codecs.graph.validate_python({})
    )
    analysis = obj["analysis"]
    ctx = Context(codecs, on_issue, strict)
    text, spans = parse_html(analysis.get("txt") or "")
    resource: Resource[R] | None = None

    if text := text or analysis.get("plain_txt"):
        resource = Resource(
            text,
            title=analysis.get("documentTitle") or None,
            source=analysis.get("documentSource") or None,
            timestamp=from_format(
                analysis.get("documentDate"), ova.DATE_FORMAT_ANALYSIS
            ),
            userdata=codecs.resource.validate_python({}),
        )
        g.add_resource(resource)

    for participant in obj["participants"]:
        g.add_participant(
            new_participant(
                codecs.participant,
                stringify_id(participant["id"]),
                participant["firstname"],
                participant["surname"],
            )
        )

    if analyst_name := analysis.get("annotatorName"):
        g.add_analyst(
            Analyst(analyst_name, userdata=codecs.analyst.validate_python({}))
        )

    for ova_node in obj["nodes"]:
        if ova_node["type"] == "I":
            atom = atom_from_ova(ova_node, codecs.atom)
            span = spans.get(f"node{atom.id}")
            atom = dataclasses.replace(
                atom,
                participant=None
                if (
                    participant := lookup(
                        ctx,
                        g.participants,
                        ova_node.get("participantID"),
                        "participant",
                        f"atom node '{atom.id}'",
                    )
                )
                is None
                else participant.id,
                reference=Reference(span.text, resource=resource.id, offset=span.offset)
                if resource and span
                else atom.reference,
            )
            add_node(g, ctx, atom)

            if (
                ova_node.get("majorClaim")
                and g.major_claim is None
                and g.atom_nodes.get(atom.id) is atom
            ):
                g.major_claim = atom

        elif scheme := scheme_from_ova(ova_node, codecs.scheme):
            add_node(g, ctx, scheme)

    # edges of dialog nodes are expected to be missing, unlike dangling ones
    dialog = {
        stringify_id(node["id"])
        for node in obj["nodes"]
        if node["type"] in aif.DIALOG_TYPES
    }

    for ova_edge in obj["edges"]:
        add_edge(
            g,
            ctx,
            stringify_id(ova_edge["from"]["id"]),
            stringify_id(ova_edge["to"]["id"]),
            uuid(),
            metadata=_metadata(ova_edge),
            ignore=dialog,
        )

    relocate(g, ctx)

    return g.freeze()


def scheme_from_ova[S](obj: ova.Node, codec: Codec[S]) -> SchemeNode[S] | None:
    """Generate SchemeNode object from OVA Node object."""
    if obj["type"] not in aif2scheme:
        return None

    return SchemeNode(
        resolve_aif_scheme(obj["type"], obj["text"]),
        # descriptors map roles to atom ids, the conclusion is not a premise
        premise_descriptors=[
            stringify_id(node_id)
            for role, node_id in obj["descriptors"].items()
            if node_id is not None and not role.casefold().startswith("s_conclusion")
        ],
        metadata=_metadata(obj),
        userdata=codec.validate_python({}),
        id=stringify_id(obj["id"]),
    )


def atom_from_ova[A](obj: ova.Node, codec: Codec[A]) -> AtomNode[A]:
    """Generate AtomNode object from OVA Node object."""
    return AtomNode(
        obj["text"],
        metadata=_metadata(obj),
        userdata=codec.validate_python({}),
        id=stringify_id(obj["id"]),
    )


def _metadata(obj: ova.Node | ova.Edge) -> Metadata:
    """Generate Metadata object from the `date` of an OVA node or edge."""
    return Metadata(from_format(obj.get("date"), ova.DATE_FORMAT))
