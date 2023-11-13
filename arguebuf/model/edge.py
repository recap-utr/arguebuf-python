import logging
import typing as t

from arguebuf.model import utils
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AbstractNode
from arguebuf.model.userdata import Userdata

log = logging.getLogger(__name__)

__all__ = ("warn_missing_nodes", "Edge")


def warn_missing_nodes(
    edge_id: t.Optional[str], source_id: t.Optional[str], target_id: t.Optional[str]
) -> None:
    log.warning(
        f"Skipping edge '{edge_id}': Source '{source_id}' or target '{target_id}' not"
        " found."
    )


class Edge:
    """Edge in AIF format. Connection from one Node object to another Node object."""

    __slots__ = (
        "_id",
        "_source",
        "_target",
        "metadata",
        "userdata",
    )

    _id: str
    _source: AbstractNode
    _target: AbstractNode
    metadata: Metadata
    userdata: Userdata

    def __init__(
        self,
        source: AbstractNode,
        target: AbstractNode,
        metadata: t.Optional[Metadata] = None,
        userdata: t.Optional[Userdata] = None,
        id: t.Optional[str] = None,
    ):
        # if isinstance(source, AtomNode) and isinstance(target, AtomNode):
        #     raise ValueError("Cannot create an edge between two atom nodes.")

        self._id = id or utils.uuid()
        self._source = source
        self._target = target
        self.metadata = metadata or Metadata()
        self.userdata = userdata or {}

        self.__post_init__()

    def __post_init__(self):
        pass

    def __eq__(self, other: t.Optional["Edge"]) -> bool:
        if other is None:
            return False

        return (
            self.id == other.id
            and self.source == other.source
            and self.target == other.target
        )

    def __hash__(self) -> int:
        return hash((self.id, self.source, self.target))

    def __str__(self) -> str:
        return str(self.id)

    def __repr__(self):
        return utils.class_repr(
            self,
            [str(self._id), f"{self._source.__repr__()}->{self._target.__repr__()}"],
        )

    @property
    def id(self) -> str:
        return self._id

    @property
    def source(self) -> AbstractNode:
        """Gives the 'From'-Node."""
        return self._source

    @property
    def target(self) -> AbstractNode:
        """Gives the 'To'-Node."""
        return self._target
