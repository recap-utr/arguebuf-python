"""Problems of graphs that the strict model cannot prevent."""

from collections.abc import Iterable

from arguebuf.locate import is_anchored
from arguebuf.model import Graph
from arguebuf.model.issue import Issue, IssueCode, issue, unresolved_reference
from arguebuf.model.node import AtomNode, AtomOrSchemeNode, SchemeNode
from arguebuf.traverse import dfs

__all__ = ("check",)


def check[A, S, E, R, P, N, G](
    graph: Graph[A, S, E, R, P, N, G], *, ignore: Iterable[IssueCode] = ()
) -> list[Issue]:
    """Find the problems of a graph that the strict model cannot prevent.

    These are untyped schemes, references that do not match their resource,
    and quality problems of the argument.

    Args:
        graph: Graph to check.
        ignore: Codes of issues that are not reported.

    Returns:
        The issues in a stable order.

    Examples:
        >>> from arguebuf import GraphDraft
        >>> g = GraphDraft()
        >>> g.add_node(AtomNode("Claim"))
        >>> [item.code for item in check(g.freeze())]
        ['orphaned-atom', 'no-major-claim']
    """
    nodes = list(graph.nodes.values())
    atoms = graph.atom_nodes.values()
    linked = [
        node
        for node in nodes
        if graph.incoming_edges(node) or graph.outgoing_edges(node)
    ]
    connected = {node.id for node in linked}
    issues: list[Issue] = []

    for node in nodes:
        if isinstance(node, SchemeNode):
            issues.extend(_check_scheme(graph, node))
        else:
            issues.extend(_check_atom(graph, node))

    issues.extend(
        issue("orphaned-atom", f"Atom '{atom.id}' has no relations.", [atom.id])
        for atom in atoms
        if atom.id not in connected
    )

    components: list[list[AtomOrSchemeNode[A, S]]] = []
    visited: set[str] = set()

    for node in linked:
        if node.id not in visited:
            component = dfs(node, graph.neighbor_nodes)
            visited.update(member.id for member in component)
            components.append(component)

    if len(components) > 1:
        issues.append(
            issue(
                "disconnected",
                f"The graph splits into {len(components)} disconnected parts.",
                [component[0].id for component in components],
            )
        )

    major_claim = graph.major_claim

    if major_claim is None:
        if atoms:
            issues.append(issue("no-major-claim", "No major claim is set."))
    else:
        ancestors = {
            node.id for node in dfs(graph.atom_nodes[major_claim], graph.incoming_nodes)
        }
        issues.extend(
            issue(
                "unreachable-major-claim",
                f"Atom '{atom.id}' is not connected to the major claim '{major_claim}'.",
                [atom.id, major_claim],
            )
            for atom in atoms
            if atom.id in connected and atom.id not in ancestors
        )

    ignored = set(ignore)

    return [item for item in issues if item.code not in ignored]


def _check_scheme[A, S, E, R, P, N, G](
    graph: Graph[A, S, E, R, P, N, G], node: SchemeNode[S]
) -> list[Issue]:
    issues: list[Issue] = []
    conclusions = len(graph.outgoing_edges(node))

    if node.scheme is None:
        issues.append(
            issue("untyped-scheme", f"Scheme '{node.id}' has no type.", [node.id])
        )

    if not graph.premise_nodes(node):
        issues.append(
            issue(
                "scheme-without-premise",
                f"Scheme '{node.id}' has no premise.",
                [node.id],
            )
        )

    if conclusions == 0:
        issues.append(
            issue(
                "scheme-without-conclusion",
                f"Scheme '{node.id}' has no conclusion.",
                [node.id],
            )
        )
    elif conclusions > 1:
        issues.append(
            issue(
                "scheme-multiple-conclusions",
                f"Scheme '{node.id}' has {conclusions} conclusions.",
                [node.id],
            )
        )

    return issues


def _check_atom[A, S, E, R, P, N, G](
    graph: Graph[A, S, E, R, P, N, G], node: AtomNode[A]
) -> list[Issue]:
    # the model ensures that the resource exists
    reference = node.reference

    if reference is None or reference.resource is None:
        return []

    text = graph.resources[reference.resource].text

    if reference.offset is None:
        return [] if reference.text in text else [
            unresolved_reference(node.id, reference.resource)
        ]

    if is_anchored(text, reference.text, reference.offset):
        return []

    return [
        issue(
            "reference-mismatch",
            f"The reference of atom '{node.id}' does not match resource '{reference.resource}' at offset {reference.offset}.",
            [node.id, reference.resource],
        )
    ]
