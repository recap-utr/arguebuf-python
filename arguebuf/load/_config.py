from __future__ import annotations

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
    GraphClass: t.Type[Graph] = Graph
    AtomNodeClass: t.Type[AtomNode] = AtomNode
    SchemeNodeClass: t.Type[SchemeNode] = SchemeNode
    EdgeClass: t.Type[Edge] = Edge
    AnalystClass: t.Type[Analyst] = Analyst
    MetadataClass: t.Type[Metadata] = Metadata
    ParticipantClass: t.Type[Participant] = Participant
    ReferenceClass: t.Type[Reference] = Reference
    ResourceClass: t.Type[Resource] = Resource


DefaultConfig = Config[str]()
