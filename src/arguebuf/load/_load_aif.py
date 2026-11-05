import dataclasses
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Self

from arguebuf._dt import from_format
from arguebuf.model import Graph, GraphDraft
from arguebuf.model.issue import Reporter
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.reference import Reference
from arguebuf.model.scheme import AIF_SCHEME_TYPES, Rephrase, resolve_aif_scheme
from arguebuf.model.userdata import DEFAULT_CODECS, Codec, Codecs, JsonObject
from arguebuf.schemas import aif

from ._helpers import (
    Context,
    add_edge,
    add_node,
    connect,
    new_participant,
    stringify_id,
)

__all__ = ("load_aif",)


def load_aif[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    obj: aif.Graph,
    *,
    name: str | None = None,
    reconstruct_dialog: bool = False,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, R, P, N, G]:
    """Generate Graph structure from AIF argument graph file.

    Dialog nodes (L, TA, YA) are skipped.
    Numeric ids are converted to strings, other numbers than integers raise an error.
    All listed participants and the speakers of locutions become participants.
    An atom asserted by locutions gets their speaker as participant
    if all locutions together have exactly one speaker,
    and the locution text as reference if there is exactly one locution.
    A missing `scheme` of a scheme node falls back to its `text`.
    With `reconstruct_dialog`, atoms only linked through dialog nodes
    are connected to the atoms of adjacent turns via rephrase nodes,
    otherwise they become isolated.
    """
    g: GraphDraft[A, S, E, R, P, N, G] = GraphDraft(
        name, userdata=codecs.graph.validate_python({})
    )
    index = _Index.from_aif(obj)
    ctx = Context(codecs, on_issue, strict)

    for participant in obj.get("participants") or []:
        g.add_participant(
            new_participant(
                codecs.participant,
                stringify_id(participant["participantID"]),
                participant.get("firstname", ""),
                participant.get("surname", ""),
            )
        )

    # a locution node may be listed several times with different speakers
    speakers: defaultdict[str, dict[str, None]] = defaultdict(dict)

    for locution in obj.get("locutions") or []:
        person = stringify_id(locution["personID"])

        if person not in g.participants:
            g.add_participant(new_participant(codecs.participant, person))

        speakers[stringify_id(locution["nodeID"])][person] = None

    for aif_node in obj["nodes"]:
        node = node_from_aif(aif_node, codecs.atom, codecs.scheme)

        if node is None:
            continue

        if isinstance(node, AtomNode):
            locutions = dict.fromkeys(index.locutions(node.id))
            participants = dict.fromkeys(
                speaker
                for locution in locutions
                for speaker in speakers.get(locution, {})
            )

            if len(participants) == 1:
                (participant,) = participants
                node = dataclasses.replace(node, participant=participant)

            if len(locutions) == 1:
                (locution,) = locutions
                node = dataclasses.replace(
                    node, reference=Reference(index.nodes[locution]["text"])
                )

        add_node(g, ctx, node)

    # edges of dialog nodes are expected to be missing, unlike dangling ones
    dialog = {
        id for id, node in index.nodes.items() if node["type"] in aif.DIALOG_TYPES
    }

    for edge_id, source, target in index.edges:
        add_edge(g, ctx, source, target, edge_id, ignore=dialog)

    if reconstruct_dialog:
        _reconstruct_dialog(g, ctx, index)

    return g.freeze()


def node_from_aif[A, S](
    obj: aif.Node, atom_codec: Codec[A], scheme_codec: Codec[S]
) -> AtomNode[A] | SchemeNode[S] | None:
    """Generate an atom or scheme node from an AIF node, None if it is a dialog node."""
    if obj["type"] != "I" and obj["type"] not in AIF_SCHEME_TYPES:
        return None

    metadata = Metadata(from_format(obj.get("timestamp"), aif.DATE_FORMAT))
    id = stringify_id(obj["nodeID"])

    if obj["type"] == "I":
        return AtomNode(
            obj["text"],
            metadata=metadata,
            userdata=atom_codec.validate_python({}),
            id=id,
        )

    return SchemeNode(
        resolve_aif_scheme(obj["type"], obj.get("scheme") or obj["text"]),
        metadata=metadata,
        userdata=scheme_codec.validate_python({}),
        id=id,
    )


@dataclass(slots=True, frozen=True)
class _Index:
    """Nodes and edges of an AIF graph with string ids."""

    nodes: Mapping[str, aif.Node]
    edges: list[tuple[str, str, str]]
    successors: Mapping[str, list[str]]
    predecessors: Mapping[str, list[str]]

    @classmethod
    def from_aif(cls, obj: aif.Graph) -> Self:
        edges = [
            (
                stringify_id(edge["edgeID"]),
                stringify_id(edge["fromID"]),
                stringify_id(edge["toID"]),
            )
            for edge in obj["edges"]
        ]
        successors: defaultdict[str, list[str]] = defaultdict(list)
        predecessors: defaultdict[str, list[str]] = defaultdict(list)

        for _, source, target in edges:
            successors[source].append(target)
            predecessors[target].append(source)

        return cls(
            {stringify_id(node["nodeID"]): node for node in obj["nodes"]},
            edges,
            successors,
            predecessors,
        )

    def type(self, id: str) -> aif.NodeType | None:
        return node["type"] if (node := self.nodes.get(id)) else None

    def follow(
        self, ids: Iterable[str], forward: bool, node_type: aif.NodeType
    ) -> list[str]:
        """Get the neighbors of the given type in the direction of the edges."""
        adjacency = self.successors if forward else self.predecessors

        return [
            neighbor
            for id in ids
            for neighbor in adjacency.get(id, [])
            if self.type(neighbor) == node_type
        ]

    def locutions(self, atom_id: str) -> list[str]:
        """Get the locutions asserting an atom via illocutions."""
        return self.follow(self.follow([atom_id], False, "YA"), False, "L")


def _reconstruct_dialog[A, S, E, R, P, N, G](
    g: GraphDraft[A, S, E, R, P, N, G], ctx: Context[A, S, E, R, P, N, G], index: _Index
) -> None:
    """Connect isolated atoms to the atoms of adjacent turns via rephrase nodes.

    In AIF+, a locution (L) asserts an atom (I) via an illocution (YA)
    and is linked to the locutions before and after it via transitions (TA).
    """
    isolated = [
        atom
        for atom in g.atom_nodes.values()
        if not g.incoming_edges(atom) and not g.outgoing_edges(atom)
    ]
    connected: set[frozenset[str]] = set()

    for atom in isolated:
        locutions = index.locutions(atom.id)

        # turns before (backward) and after (forward) the locutions
        for forward in (False, True):
            transitions = index.follow(locutions, forward, "TA")
            turns = index.follow(transitions, forward, "L")
            illocutions = index.follow(turns, True, "YA")

            for target in index.follow(illocutions, True, "I"):
                pair = frozenset((atom.id, target))

                if target != atom.id and pair not in connected:
                    connected.add(pair)
                    scheme = SchemeNode(
                        Rephrase.DEFAULT,
                        userdata=ctx.codecs.scheme.validate_python({}),
                    )
                    g.add_node(scheme)
                    connect(g, ctx, [atom.id], scheme.id, target)
