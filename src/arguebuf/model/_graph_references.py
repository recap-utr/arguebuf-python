import dataclasses

from arguebuf.locate import is_anchored, locate
from arguebuf.model._graph_store import GraphStore, touched
from arguebuf.model.issue import Issue, issue, unresolved_reference
from arguebuf.model.reference import Reference

__all__ = ("relocate_references",)


def relocate_references[A, S, E, R, P, N](
    store: GraphStore[A, S, E, R, P, N], *, resource: str | None, threshold: float
) -> list[Issue]:
    """See `Graph.relocate_references`."""
    issues: list[Issue] = []

    for node in list(store.atom_nodes.values()):
        reference = node.reference
        source = reference.resource if reference else None

        if (
            reference is None
            or source is None
            or (resource is not None and source != resource)
            or is_anchored(
                text := store.resources[source].text, reference.text, reference.offset
            )
        ):
            continue

        match = locate(text, reference.text, threshold=threshold, near=reference.offset)

        if match is None:
            issues.append(unresolved_reference(node.id, source))
        elif match.text != reference.text or reference.offset is not None:
            issues.append(
                issue(
                    "reference-mismatch",
                    f"The reference of atom '{node.id}' was moved to offset {match.offset} of resource '{source}'.",
                    [node.id, source],
                )
            )

        store.replace_node(
            dataclasses.replace(
                node,
                reference=Reference(
                    match.text if match else reference.text,
                    resource=source,
                    offset=match.offset if match else None,
                ),
                metadata=touched(node.metadata),
            )
        )

    return issues
