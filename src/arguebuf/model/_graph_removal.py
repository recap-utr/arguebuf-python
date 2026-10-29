"""Removal of graph elements, cascading to the references to them and to dangling scheme nodes."""

import dataclasses
from collections.abc import Callable, Iterable, Mapping
from collections.abc import Set as AbstractSet

from arguebuf.model._graph_store import GraphStore, touched
from arguebuf.model.issue import fail
from arguebuf.model.node import AtomNode, AtomOrSchemeNode
from arguebuf.model.reference import Reference
from arguebuf.traverse import dfs

__all__ = ("remove_branch", "remove_elements", "remove_participant", "remove_resource")


def remove_elements[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], ids: Iterable[str]
) -> None:
    """See `Graph.remove_elements`."""
    ids = list(dict.fromkeys(ids))
    kinds: tuple[Mapping[str, object], ...] = (
        store.nodes,
        store.edges,
        store.resources,
        store.participants,
    )

    for id in ids:
        if not any(id in kind for kind in kinds):
            fail("unknown-element", f"Element '{id}' does not exist.", [id])

    removed_atoms: set[str] = set()

    for id in ids:
        if id in store.nodes:
            if isinstance(_remove_cascading(store, id), AtomNode):
                removed_atoms.add(id)
        elif id in store.edges:
            store.delete_edge(id)
        elif id in store.resources:
            remove_resource(store, id)
        elif id in store.participants:
            remove_participant(store, id)

    _remove_premise_descriptors(store, removed_atoms)


def _remove_cascading[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], node_id: str
) -> AtomOrSchemeNode[A, S]:
    """Remove a node and the scheme nodes left without a premise or a conclusion."""
    pending = store.neighbor_ids(node_id)
    removed = store.delete_node(node_id)

    while pending:
        id = pending.pop()

        if store.is_dangling(id):
            pending.extend(store.neighbor_ids(id))
            store.delete_node(id)

    return removed


def _remove_premise_descriptors[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], ids: AbstractSet[str]
) -> None:
    """Remove the atoms from the premise descriptors, which only reference atom nodes."""
    if not ids:
        return

    for scheme in list(store.scheme_nodes.values()):
        if not ids.isdisjoint(scheme.premise_descriptors):
            store.replace_node(
                dataclasses.replace(
                    scheme,
                    premise_descriptors=(
                        id for id in scheme.premise_descriptors if id not in ids
                    ),
                    metadata=touched(scheme.metadata),
                )
            )


def _update_atoms[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N],
    update: Callable[[AtomNode[A]], AtomNode[A] | None],
) -> None:
    """Replace the atom nodes for which `update` returns a changed node."""
    for node in list(store.atom_nodes.values()):
        if (updated := update(node)) is not None:
            store.replace_node(
                dataclasses.replace(updated, metadata=touched(node.metadata))
            )


def remove_resource[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], resource_id: str
) -> None:
    """Remove an existing resource and unset it in the references of all atom nodes."""
    del store.own_resources()[resource_id]
    _update_atoms(
        store,
        lambda node: (
            dataclasses.replace(node, reference=Reference(node.reference.text))
            if node.reference and node.reference.resource == resource_id
            else None
        ),
    )


def remove_participant[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], participant_id: str
) -> None:
    """Remove an existing participant and unset it for all its atom nodes."""
    del store.own_participants()[participant_id]
    _update_atoms(
        store,
        lambda node: (
            dataclasses.replace(node, participant=None)
            if node.participant == participant_id
            else None
        ),
    )


def remove_branch[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], start: AtomOrSchemeNode[A, S]
) -> None:
    """See `Graph.remove_branch`."""
    removed = dfs(
        start,
        lambda node: dict.fromkeys(
            store.nodes[store.edges[id].source] for id in store.incoming[node.id]
        ),
    )

    for node in removed:
        store.delete_node(node.id)

    _remove_premise_descriptors(
        store, {node.id for node in removed if isinstance(node, AtomNode)}
    )
