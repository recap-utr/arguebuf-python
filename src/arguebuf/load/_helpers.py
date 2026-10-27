"""Shared helpers for loaders that skip dangling data with a warning."""

import logging
from collections.abc import Iterable, Mapping
from collections.abc import Set as AbstractSet

from arguebuf.model import Graph
from arguebuf.model.edge import Edge
from arguebuf.model.metadata import Metadata
from arguebuf.model.participant import Participant
from arguebuf.model.reference import Reference
from arguebuf.model.resource import AbstractResource
from arguebuf.model.userdata import Codec, Codecs, JsonObject

log = logging.getLogger("arguebuf.load")

__all__ = (
    "add_edge",
    "compact",
    "connect",
    "log",
    "lookup",
    "new_participant",
    "new_reference",
    "stringify_id",
)


def stringify_id(value: str | float) -> str:
    """Convert an id of a JSON format to a string, numbers must be safe integers.

    Examples:
        >>> stringify_id(1), stringify_id(2.0), stringify_id("a")
        ('1', '2', 'a')
        >>> stringify_id(1.5)
        Traceback (most recent call last):
        ValueError: ...
    """
    if isinstance(value, str):
        return value

    if (
        isinstance(value, bool)
        or not -(2**53 - 1) <= value <= 2**53 - 1
        or not float(value).is_integer()
    ):
        raise ValueError(f"The id {value!r} is neither a string nor a safe integer.")

    return str(int(value))


def new_participant[P](codec: Codec[P], id: str, *names: str) -> Participant[P]:
    """Create a participant without userdata named by joining the non-empty `names`."""
    return Participant(
        " ".join(filter(None, names)) or None,
        userdata=codec.validate_python({}),
        id=id,
    )


def lookup[K, V](
    elements: Mapping[K, V], id: K | None, kind: str, owner: str
) -> V | None:
    """Get the element referenced by `owner`, warning if the id is unknown.

    Missing ids (None or empty) are returned as None without a warning.
    """
    if not id:
        return None

    if (element := elements.get(id)) is None:
        log.warning("Skipping unknown %s '%s' referenced by %s.", kind, id, owner)

    return element


def new_reference(
    text: str,
    resource_id: str | None,
    offset: int | None,
    resources: Mapping[str, AbstractResource],
    owner: str,
) -> Reference:
    """Create a reference, an unknown resource is skipped with a warning together with the offset.

    A missing resource id (None or empty) keeps the offset.
    """
    resource = lookup(resources, resource_id, "resource", owner)

    return Reference(
        text,
        resource=resource,
        offset=None if resource_id and resource is None else offset,
    )


def add_edge[A, S, E, G, R, P, N](
    g: Graph[A, S, E, G, R, P, N],
    codecs: Codecs[A, S, E, G, R, P, N],
    source_id: str,
    target_id: str,
    id: str,
    metadata: Metadata | None = None,
    userdata: JsonObject | None = None,
    ignore: AbstractSet[str] = frozenset(),
) -> None:
    """Connect two nodes by their ids, skipping the edge with a warning if one is missing.

    Edges of the intentionally skipped nodes in `ignore` are skipped silently.
    The edge codec only loads the userdata of edges that are added.
    """
    if source_id in ignore or target_id in ignore:
        return

    if source_id not in g.nodes or target_id not in g.nodes:
        log.warning(
            "Skipping edge '%s': Source '%s' or target '%s' not found.",
            id,
            source_id,
            target_id,
        )

        return

    g.add_edge(
        Edge(
            g.nodes[source_id],
            g.nodes[target_id],
            metadata=metadata,
            userdata=codecs.edge.validate_python(userdata or {}),
            id=id,
        )
    )


def connect[A, S, E, G, R, P, N](
    g: Graph[A, S, E, G, R, P, N],
    codecs: Codecs[A, S, E, G, R, P, N],
    source_ids: Iterable[str],
    scheme_id: str,
    target_id: str,
) -> None:
    """Connect the sources to the target through the scheme node, all given by their ids.

    The scheme node must already be part of the graph.
    Edge ids are derived from the node ids as `source->target`,
    edges of missing nodes are skipped with a warning.
    """
    for source_id in source_ids:
        add_edge(g, codecs, source_id, scheme_id, f"{source_id}->{scheme_id}")

    add_edge(g, codecs, scheme_id, target_id, f"{scheme_id}->{target_id}")


def compact[V](fields: Mapping[str, V | None]) -> dict[str, V]:
    """Drop the fields whose value is None.

    Examples:
        >>> compact({"a": 1, "b": None})
        {'a': 1}
    """
    return {key: value for key, value in fields.items() if value is not None}
