import typing as t
from dataclasses import dataclass

from arguebuf.model import Graph
from arguebuf.model.analyst import Analyst
from arguebuf.model.edge import Edge
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.reference import Reference
from arguebuf.model.resource import Resource
from arguebuf.model.typing import TextType

__all__ = ("Config",)


@dataclass
class Config(t.Generic[TextType]):
    nlp: t.Optional[t.Callable[[str], TextType]] = None
    GraphClass: type[Graph] = Graph
    AtomNodeClass: type[AtomNode] = AtomNode
    SchemeNodeClass: type[SchemeNode] = SchemeNode
    EdgeClass: type[Edge] = Edge
    AnalystClass: type[Analyst] = Analyst
    MetadataClass: type[Metadata] = Metadata
    ParticipantClass: type[Participant] = Participant
    ReferenceClass: type[Reference] = Reference
    ResourceClass: type[Resource] = Resource


DefaultConfig = Config[str]()
