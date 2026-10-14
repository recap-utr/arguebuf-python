import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from arguebuf.dt import now
from arguebuf.model import Graph
from arguebuf.model.analyst import Analyst
from arguebuf.model.edge import Edge
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.reference import Reference
from arguebuf.model.resource import Resource
from arguebuf.model.userdata import Userdata

log = logging.getLogger(__name__)

__all__ = ("Config",)


@dataclass(slots=True, frozen=True)
class Config[T = str]:
    """Options for loading graphs.

    Attributes:
        nlp: Transforms all texts of atom nodes, references, and resources,
            e.g., to compute embeddings with `spacy.load(...)`.
        reconstruct_dialog: Connect atoms of AIF and xAIF graphs that are only linked
            through dialog nodes (L, TA, YA) to the atoms of adjacent turns
            via rephrase nodes, otherwise they become isolated.
        GraphClass: Class used for graphs, allows using specialized subclasses.
            The same applies to all other `*Class` attributes.
    """

    nlp: Callable[[str], T] | None = None
    reconstruct_dialog: bool = False
    GraphClass: type[Graph[T]] = Graph[T]
    AtomNodeClass: type[AtomNode[T]] = AtomNode[T]
    SchemeNodeClass: type[SchemeNode] = SchemeNode
    EdgeClass: type[Edge] = Edge
    AnalystClass: type[Analyst] = Analyst
    MetadataClass: type[Metadata] = Metadata
    ParticipantClass: type[Participant] = Participant
    ReferenceClass: type[Reference[T]] = Reference[T]
    ResourceClass: type[Resource[T]] = Resource[T]

    def parse(self, text: str | None) -> T:
        """Apply `nlp` to the text, returns the text unchanged if `nlp` is not set."""
        if self.nlp is None:
            # without nlp, T is str
            return cast(T, text)

        try:
            return self.nlp(text or "")
        except ValueError:
            return self.nlp("")

    def graph(self, name: str | None) -> Graph[T]:
        """Create a graph, generating a name if none is given."""
        return self.GraphClass(name) if name else self.GraphClass()

    def participant(self, id: str, *names: str) -> Participant:
        """Create a participant named by joining the non-empty `names`."""
        return self.ParticipantClass(" ".join(filter(None, names)) or None, id=id)

    def metadata(self, timestamp: datetime | None) -> Metadata:
        """Create metadata created and updated at `timestamp`, defaulting to now."""
        timestamp = timestamp or now()

        return self.MetadataClass(timestamp, timestamp)

    def edge(
        self,
        nodes: Mapping[str, AbstractNode],
        source_id: str,
        target_id: str,
        id: str,
        metadata: Metadata | None = None,
        userdata: Userdata | None = None,
    ) -> Edge | None:
        """Connect two nodes by their ids, skipping the edge if one is missing."""
        if source_id not in nodes or target_id not in nodes:
            log.warning(
                "Skipping edge '%s': Source '%s' or target '%s' not found.",
                id,
                source_id,
                target_id,
            )

            return None

        return self.EdgeClass(
            nodes[source_id],
            nodes[target_id],
            metadata=metadata or self.MetadataClass(),
            userdata=userdata or {},
            id=id,
        )

    def connect(
        self,
        graph: Graph[T],
        source: AbstractNode,
        scheme: SchemeNode,
        target: AbstractNode,
    ) -> None:
        """Connect `source` to `target` via the scheme node."""
        graph.add_edge(self.EdgeClass(source, scheme))
        graph.add_edge(self.EdgeClass(scheme, target))
