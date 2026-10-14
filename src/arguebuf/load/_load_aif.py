from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Self

from arguebuf.dt import from_format
from arguebuf.model import Graph
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.scheme import Rephrase, aif2scheme, resolve_aif_scheme
from arguebuf.schemas import aif

from ._config import Config

__all__ = ("load_aif",)


def load_aif[T = str](
    obj: aif.Graph, name: str | None = None, config: Config[T] = Config()
) -> Graph[T]:
    """Generate Graph structure from AIF argument graph file.

    Dialog nodes (L, TA, YA) are skipped,
    but an atom asserted by exactly one locution gets its speaker as participant
    and the locution text as reference.
    See `Config.reconstruct_dialog` to keep the atoms that dialog nodes connect.
    """
    g = config.graph(name)
    index = _Index.from_aif(obj)
    names = {
        str(participant["participantID"]): (
            participant["firstname"],
            participant["surname"],
        )
        for participant in obj.get("participants") or []
    }
    speakers: dict[str, Participant] = {}

    for locution in obj["locutions"] or []:
        person = str(locution["personID"])

        if person not in g.participants:
            g.add_participant(config.participant(person, *names.get(person, ())))

        speakers[str(locution["nodeID"])] = g.participants[person]

    for aif_node in obj["nodes"]:
        node = node_from_aif(aif_node, config)

        if node is None:
            continue

        if isinstance(node, AtomNode):
            match index.locutions(node.id):
                case [locution]:
                    node.participant = speakers.get(locution)
                    node.reference = config.ReferenceClass(
                        config.parse(index.nodes[locution]["text"])
                    )

        g.add_node(node)

    for edge_id, source, target in index.edges:
        # edges of dialog nodes are expected to be missing, unlike dangling ones
        if aif.DIALOG_TYPES.isdisjoint((index.type(source), index.type(target))) and (
            edge := config.edge(g.nodes, source, target, edge_id)
        ):
            g.add_edge(edge)

    if config.reconstruct_dialog:
        _reconstruct_dialog(g, index, config)

    return g


def node_from_aif[T](
    obj: aif.Node, config: Config[T]
) -> AtomNode[T] | SchemeNode | None:
    """Generate an atom or scheme node from an AIF node, None if it is a dialog node."""
    if obj["type"] != "I" and obj["type"] not in aif2scheme:
        return None

    metadata = config.metadata(from_format(obj.get("timestamp"), aif.DATE_FORMAT))
    id = str(obj["nodeID"])

    if obj["type"] == "I":
        return config.AtomNodeClass(config.parse(obj["text"]), metadata=metadata, id=id)

    return config.SchemeNodeClass(
        resolve_aif_scheme(obj["type"], obj.get("scheme", obj["text"])),
        metadata=metadata,
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
            (str(edge["edgeID"]), str(edge["fromID"]), str(edge["toID"]))
            for edge in obj["edges"]
        ]
        successors: defaultdict[str, list[str]] = defaultdict(list)
        predecessors: defaultdict[str, list[str]] = defaultdict(list)

        for _, source, target in edges:
            successors[source].append(target)
            predecessors[target].append(source)

        return cls(
            {str(node["nodeID"]): node for node in obj["nodes"]},
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


def _reconstruct_dialog[T](g: Graph[T], index: _Index, config: Config[T]) -> None:
    """Connect isolated atoms to the atoms of adjacent turns via rephrase nodes.

    In AIF+, a locution (L) asserts an atom (I) via an illocution (YA)
    and is linked to the locutions before and after it via transitions (TA).
    """
    isolated_nodes = g.root_nodes & g.leaf_nodes
    isolated = [atom for atom in g.atom_nodes.values() if atom in isolated_nodes]
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
                    scheme = config.SchemeNodeClass(
                        Rephrase.DEFAULT, metadata=config.metadata(None)
                    )
                    config.connect(g, atom, scheme, g.atom_nodes[target])
