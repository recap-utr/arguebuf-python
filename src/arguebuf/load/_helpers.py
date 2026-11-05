"""Shared helpers for loaders that repair or skip malformed data and report it."""

import copy
from collections.abc import Callable, Iterable, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from typing import Protocol

from arguebuf.model import GraphDraft
from arguebuf.model.edge import Edge
from arguebuf.model.issue import (
    GraphError,
    Issue,
    IssueCode,
    Reporter,
    catch_graph_error,
    issue,
    warn,
)
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import Node, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.reference import Reference
from arguebuf.model.userdata import Codec, Codecs, JsonObject
from arguebuf.model.utils import Entity

__all__ = (
    "Context",
    "add_edge",
    "add_node",
    "compact",
    "connect",
    "lookup",
    "new_participant",
    "new_reference",
    "relocate",
    "stringify_id",
)


class Reporting(Protocol):
    """Reports a repaired or skipped element as warning."""

    def report(
        self, code: IssueCode, message: str, elements: Iterable[str] = ()
    ) -> None:
        """Report the issue to the reporter of the loader."""
        ...


@dataclass(slots=True, frozen=True)
class Context[A, S, E, R, P, N, G]:
    """Codecs and reporting options of a loader.

    Attributes:
        codecs: Codecs loading the userdata.
        on_issue: Receives the repairs and skipped elements as warnings,
            defaults to logging them.
        strict: Raise a `GraphError` instead of repairing or skipping malformed data.
    """

    codecs: Codecs[A, S, E, R, P, N, G]
    on_issue: Reporter | None = None
    strict: bool = False

    def report(
        self, code: IssueCode, message: str, elements: Iterable[str] = ()
    ) -> None:
        """Report a repaired or skipped element as warning."""
        item = issue(code, message, elements, severity="warning")

        if self.strict:
            raise GraphError(copy.replace(item, severity="error"))

        (self.on_issue or warn)(item)

    def attempt(
        self, action: Callable[[], object], consequence: Callable[[Issue], str]
    ) -> Issue | None:
        """Run the action and report its `GraphError` together with the consequence of skipping it."""
        if (error := catch_graph_error(action)) is not None:
            self.report(
                error.code, f"{error.message} {consequence(error)}", error.elements
            )

        return error


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
    ctx: Reporting, elements: Mapping[K, V], id: K | None, kind: str, owner: str
) -> V | None:
    """Get the element referenced by `owner`, warning if the id is unknown.

    Missing ids (None or empty) are returned as None without a warning.
    """
    if not id:
        return None

    if (element := elements.get(id)) is None:
        ctx.report(
            "unknown-element",
            f"Skipping unknown {kind} '{id}' referenced by {owner}.",
            [str(id)],
        )

    return element


def new_reference(
    ctx: Reporting,
    text: str,
    resource_id: str | None,
    offset: int | None,
    resources: Mapping[str, Entity],
    owner: str,
) -> Reference:
    """Create a reference, an unknown resource is skipped with a warning together with the offset.

    A missing resource id (None or empty) keeps the offset.
    """
    resource = lookup(ctx, resources, resource_id, "resource", owner)

    return Reference(
        text,
        resource=resource_id if resource is not None else None,
        offset=None if resource_id and resource is None else offset,
    )


def add_node[A, S, E, R, P, N, G](
    g: GraphDraft[A, S, E, R, P, N, G],
    ctx: Context[A, S, E, R, P, N, G],
    node: Node[A, S],
) -> None:
    """Add a node, skipping it with a warning if it is invalid, e.g. if its id is taken."""
    ctx.attempt(lambda: g.add_node(node), lambda _: "The node was skipped.")


def add_edge[A, S, E, R, P, N, G](
    g: GraphDraft[A, S, E, R, P, N, G],
    ctx: Context[A, S, E, R, P, N, G],
    source_id: str,
    target_id: str,
    id: str,
    metadata: Metadata | None = None,
    userdata: JsonObject | None = None,
    ignore: AbstractSet[str] = frozenset(),
) -> None:
    """Connect two nodes by their ids, repairing or skipping the edge with a warning if it is invalid.

    An edge between two atom nodes is replaced by an untyped scheme,
    other invalid edges are skipped.
    Edges of the intentionally skipped nodes in `ignore` are skipped silently.
    """
    if source_id in ignore or target_id in ignore:
        return

    edge = Edge(
        source_id,
        target_id,
        metadata=metadata,
        userdata=ctx.codecs.edge.validate_python(userdata or {}),
        id=id,
    )

    error = ctx.attempt(
        lambda: g.add_edge(edge),
        lambda error: (
            "An untyped scheme was inserted."
            if error.code == "atom-edge"
            else "The edge was skipped."
        ),
    )

    if error is not None and error.code == "atom-edge":
        scheme = SchemeNode(userdata=ctx.codecs.scheme.validate_python({}))
        g.add_node(scheme)
        g.add_edge(
            Edge(
                source_id,
                scheme.id,
                id=edge.id,
                metadata=edge.metadata,
                userdata=edge.userdata,
            )
        )
        g.add_edge(
            Edge(scheme.id, target_id, metadata=edge.metadata, userdata=edge.userdata)
        )


def connect[A, S, E, R, P, N, G](
    g: GraphDraft[A, S, E, R, P, N, G],
    ctx: Context[A, S, E, R, P, N, G],
    source_ids: Iterable[str],
    scheme_id: str,
    target_id: str,
) -> None:
    """Connect the sources to the target through the scheme node, all given by their ids.

    The scheme node must already be part of the graph.
    Edge ids are derived from the node ids as `source->target`,
    invalid edges are skipped with a warning.
    """
    for source_id in source_ids:
        add_edge(g, ctx, source_id, scheme_id, f"{source_id}->{scheme_id}")

    add_edge(g, ctx, scheme_id, target_id, f"{scheme_id}->{target_id}")


def relocate[A, S, E, R, P, N, G](
    g: GraphDraft[A, S, E, R, P, N, G], ctx: Context[A, S, E, R, P, N, G]
) -> None:
    """Re-anchor references that do not match their resource, see `GraphDraft.relocate_references`."""
    for item in g.relocate_references():
        ctx.report(item.code, item.message, item.elements)


def compact[V](fields: Mapping[str, V | None]) -> dict[str, V]:
    """Drop the fields whose value is None.

    Examples:
        >>> compact({"a": 1, "b": None})
        {'a': 1}
    """
    return {key: value for key, value in fields.items() if value is not None}
