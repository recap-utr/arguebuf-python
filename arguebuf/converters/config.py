from __future__ import annotations

import typing as t
from dataclasses import dataclass
from enum import Enum

from arguebuf.models.analyst import Analyst
from arguebuf.models.edge import Edge
from arguebuf.models.graph import Graph
from arguebuf.models.metadata import Metadata
from arguebuf.models.node import AtomNode, SchemeNode
from arguebuf.models.participant import Participant
from arguebuf.models.reference import Reference
from arguebuf.models.resource import Resource
from arguebuf.models.typing import TextType


@dataclass
class ConverterConfig(t.Generic[TextType]):
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


DefaultConverter = ConverterConfig[str]()


class GraphFormat(str, Enum):
    ARGUEBUF = "arguebuf"
    AIF = "aif"
