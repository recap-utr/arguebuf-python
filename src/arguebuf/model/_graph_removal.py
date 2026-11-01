"""Removal of graph elements, cascading to the references to them and to dangling scheme nodes."""

import dataclasses
from collections.abc import Callable, Iterable, Mapping

from arguebuf.model._graph_store import GraphStore, touched
from arguebuf.model.issue import fail
from arguebuf.model.node import AtomNode, AtomOrSchemeNode
from arguebuf.model.reference import Reference
from arguebuf.traverse import dfs

__all__ = ("remove_branches", "remove_elements", "remove_participant", "remove_resource")

# ids of removed elements, a dict keeps their order
type _Removed = dict[str, None]


def remove_elements[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], ids: Iterable[str]
) -> list[str]:
    """See `GraphDraft.remove_elements`."""
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

    removed: _Removed = {}

    for id in ids:
        if id in store.nodes:
            _remove_cascading(store, id, removed)
        elif id in store.edges:
            store.delete_edge(id)
        elif id in store.resources:
            remove_resource(store, id)
        elif id in store.participants:
            remove_participant(store, id)
        else:
            # removed by a cascade earlier in the loop
            continue

        removed[id] = None

    return _finish(store, removed)


def _delete_node[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], node_id: str, removed: _Removed
) -> None:
    """Delete the node with its edges, collecting their ids."""
    removed[node_id] = None
    removed.update(store.incoming[node_id])
    removed.update(store.outgoing[node_id])
    store.delete_node(node_id)


def _remove_cascading[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], node_id: str, removed: _Removed
) -> None:
    """Remove a node and the scheme nodes left without a premise or a conclusion."""
    pending = store.neighbor_ids(node_id)
    _delete_node(store, node_id, removed)

    while pending:
        id = pending.pop()

        if store.is_dangling(id):
            pending.extend(store.neighbor_ids(id))
            _delete_node(store, id, removed)


def _finish[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], removed: _Removed
) -> list[str]:
    """Remove the removed atoms from the premise descriptors and return the removed ids."""
    # other kinds of elements may share the id of a remaining atom
    atoms = removed.keys() - store.atom_nodes.keys()

    for scheme in list(store.scheme_nodes.values()):
        if not atoms.isdisjoint(scheme.premise_descriptors):
            store.replace_node(
                dataclasses.replace(
                    scheme,
                    premise_descriptors=(
                        id for id in scheme.premise_descriptors if id not in atoms
                    ),
                    metadata=touched(scheme.metadata),
                )
            )

    return list(removed)


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


def remove_branches[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], starts: Iterable[AtomOrSchemeNode[A, S]]
) -> list[str]:
    """See `GraphDraft.remove_branch`, the branches of all starts are removed at once."""
    removed: _Removed = {}

    for start in starts:
        # a branch removed before may contain this one
        if start.id not in store.nodes:
            continue

        branch = dfs(
            start,
            lambda node: dict.fromkeys(
                store.nodes[store.edges[id].source] for id in store.incoming[node.id]
            ),
        )

        for node in branch:
            _delete_node(store, node.id, removed)

    return _finish(store, removed)
