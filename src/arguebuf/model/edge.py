from dataclasses import KW_ONLY, dataclass, field

from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AbstractNode
from arguebuf.model.userdata import Userdata
from arguebuf.model.utils import Entity, uuid

__all__ = ("Edge",)


@dataclass(slots=True, frozen=True, eq=False)
class Edge(Entity):
    """Directed connection from a source node to a target node."""

    source: AbstractNode
    target: AbstractNode
    _: KW_ONLY
    metadata: Metadata = field(default_factory=Metadata, repr=False)
    userdata: Userdata = field(default_factory=dict, repr=False)
    id: str = field(default_factory=uuid)
