import copy
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import partial

from pydantic import ValidationError

from arguebuf.locate import DEFAULT_THRESHOLD
from arguebuf.model import Graph, GraphDraft
from arguebuf.model.issue import Issue, catch_graph_error, fail, has_errors, issue
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.resource import Resource
from arguebuf.model.scheme import SCHEME_CLASSES
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs
from arguebuf.patch._resolve import link_text, resolve_scheme_of
from arguebuf.patch._schema import (
    AtomPatch,
    ParticipantPatch,
    Patch,
    ResourcePatch,
    SchemePatch,
)

__all__ = ("PatchResult", "apply_patch")

type Path = tuple[str | int, ...]


@dataclass(slots=True, frozen=True)
class PatchResult[A, S, E, R, P, N, G]:
    """Result of `apply_patch`.

    The ids cover nodes, resources, and participants and are empty if there are errors.

    Attributes:
        graph: The changed graph, or the input if there are errors.
        issues: Errors and warnings, each pointing to its item via `path`.
        created: Ids of the new elements.
        updated: Ids of the existing elements that the patch replaced.
        removed: Ids of the removed elements, including those removed by cascades.
    """

    graph: Graph[A, S, E, R, P, N, G]
    issues: tuple[Issue, ...] = ()
    created: tuple[str, ...] = ()
    updated: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()


@dataclass(slots=True)
class _Editor[A, S, E, R, P, N, G]:
    graph: GraphDraft[A, S, E, R, P, N, G]
    codecs: Codecs[A, S, E, R, P, N, G]
    threshold: float
    issues: list[Issue] = field(default_factory=list)

    def apply(self, patch: Patch) -> None:
        graph = self.graph

        cleared = list(graph.nodes) if patch.clear else []

        # removals cascade, so ids that a cascade already removed are skipped
        self._attempt(
            ("delete",), partial(graph.remove_elements, [*cleared, *patch.delete])
        )
        self._each("resources", patch.resources, self._resource)
        self._each("participants", patch.participants, self._participant)
        self._each("atoms", patch.atoms, self._atom)

        # all schemes exist before they are wired, so that schemes can target schemes
        added = self._each("schemes", patch.schemes, self._scheme)

        for index, (item, ok) in enumerate(zip(patch.schemes, added, strict=True)):
            if ok:
                self._attempt(("schemes", index), partial(self._wire, item))

        if (major_claim := patch.major_claim) is not None:
            self._attempt(
                ("majorClaim",), partial(setattr, graph, "major_claim", major_claim)
            )

    def _each[T](
        self, key: str, items: Sequence[T], action: Callable[[T, Path], None]
    ) -> list[bool]:
        """Apply the action to each item, returns whether each one succeeded."""
        return [
            self._attempt((key, index), partial(action, item, (key, index)))
            for index, item in enumerate(items)
        ]

    def _attempt(self, path: Path, action: Callable[[], object]) -> bool:
        """Run the action and record its `GraphError`, returns whether it succeeded."""
        if (error := catch_graph_error(action)) is not None:
            self.issues.append(copy.replace(error, path=path))

        return error is None

    def _warn(self, path: Path, warning: Issue | None) -> None:
        if warning is not None:
            self.issues.append(copy.replace(warning, path=path))

    def _find[T: AbstractNode](self, id: str, nodes: Mapping[str, T]) -> T | None:
        """The node with the id from `nodes`, the atom or scheme nodes of the graph.

        A node of the other type is rejected.
        """
        if id in nodes or (node := self.graph.nodes.get(id)) is None:
            return nodes.get(id)

        actual, expected = (
            ("an atom", "a scheme")
            if isinstance(node, AtomNode)
            else ("a scheme", "an atom")
        )
        fail("invalid-patch", f"Node '{id}' is {actual}, not {expected}.", [id])

    def _resource(self, item: ResourcePatch, _: Path) -> None:
        graph = self.graph

        if item.id in graph.resources:
            self.issues.extend(
                graph.update_resource(
                    item.id,
                    threshold=self.threshold,
                    text=item.text,
                    title=item.title,
                    source=item.source,
                )
            )
        else:
            graph.add_resource(
                Resource(
                    item.text,
                    title=item.title,
                    source=item.source,
                    userdata=self.codecs.resource.validate_python({}),
                    id=item.id,
                )
            )

    def _participant(self, item: ParticipantPatch, _: Path) -> None:
        graph = self.graph

        if item.id not in graph.participants:
            graph.add_participant(
                Participant(
                    userdata=self.codecs.participant.validate_python({}), id=item.id
                )
            )

        graph.update_participant(
            item.id,
            name=item.name,
            username=item.username,
            email=item.email,
            url=item.url,
            location=item.location,
            description=item.description,
        )

    def _atom(self, item: AtomPatch, path: Path) -> None:
        graph = self.graph
        atom = self._find(item.id, graph.atom_nodes)

        reference = atom.reference if atom is not None else None

        # an unchanged atom keeps its reference, which may have been chosen by hand
        if (
            atom is None
            or atom.text != item.text
            or item.resource not in (None, reference.resource if reference else None)
        ):
            link = link_text(
                graph.resources, item.id, item.text, item.resource, self.threshold
            )
            self._warn(path, link.warning)
            reference = link.reference

        if atom is None:
            graph.add_node(
                AtomNode(
                    item.text,
                    participant=item.participant,
                    reference=reference,
                    userdata=self.codecs.atom.validate_python({}),
                    id=item.id,
                )
            )
        else:
            graph.update_atom(
                atom, text=item.text, reference=reference, participant=item.participant
            )

    def _scheme(self, item: SchemePatch, path: Path) -> None:
        """Create or replace the scheme node, it is wired afterwards."""
        resolved = resolve_scheme_of(item.id, SCHEME_CLASSES[item.type], item.scheme)
        self._warn(path, resolved.warning)
        node = self._find(item.id, self.graph.scheme_nodes)

        if node is None:
            self.graph.add_node(
                SchemeNode(
                    resolved.scheme,
                    userdata=self.codecs.scheme.validate_python({}),
                    id=item.id,
                )
            )
        else:
            self.graph.update_scheme(node, scheme=resolved.scheme)

    def _wire(self, item: SchemePatch) -> None:
        """Replace the premises and the conclusion.

        Premises are atoms, schemes targeting this scheme (e.g. undercutters) are kept.
        """
        graph = self.graph
        id, conclusion = item.id, item.conclusion

        for premise in item.premises:
            if self._find(premise, graph.atom_nodes) is None:
                fail(
                    "unknown-element",
                    f"Premise '{premise}' of scheme '{id}' does not exist.",
                    [id, premise],
                )

        if conclusion not in graph.nodes:
            fail(
                "unknown-element",
                f"Conclusion '{conclusion}' of scheme '{id}' does not exist.",
                [id, conclusion],
            )

        if conclusion in item.premises:
            fail(
                "invalid-patch",
                f"Scheme '{id}' uses its conclusion '{conclusion}' as premise.",
                [id, conclusion],
            )

        for edge in list(graph.incoming_edges(id)):
            if edge.source in graph.atom_nodes:
                graph.remove_edge(edge)

        for edge in list(graph.outgoing_edges(id)):
            graph.remove_edge(edge)

        graph.connect(
            item.premises,
            id,
            conclusion,
            edge_userdata=lambda: self.codecs.edge.validate_python({}),
        )


def apply_patch[A, S, E, R, P, N, G](
    graph: Graph[A, S, E, R, P, N, G],
    patch: Patch | Mapping[str, object],
    *,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    threshold: float = DEFAULT_THRESHOLD,
) -> PatchResult[A, S, E, R, P, N, G]:
    """Apply a patch to a graph, all or nothing.

    A mapping such as the arguments of a tool call is validated as `Patch`,
    problems are `invalid-patch` errors.
    The patch is applied to a draft of the graph (see `Graph.draft`),
    so the result shares the unchanged elements with the input.
    Texts of atoms are linked to the most similar spans of the resources (see `locate`).

    Args:
        graph: Graph to apply the patch to.
        patch: Changes referencing elements by id.
        codecs: Codecs creating the userdata of new elements.
        threshold: Minimal similarity of the spans linked to atoms.

    Returns:
        The changed graph, the issues, and the ids of the changed elements,
        or the input graph if an issue is an error.

    Examples:
        >>> patch = {"atoms": [{"id": "a", "text": "Claim"}], "majorClaim": "a"}
        >>> result = apply_patch(Graph(), patch)
        >>> result.graph.major_claim, result.issues, result.created
        ('a', (), ('a',))
    """
    try:
        parsed = Patch.model_validate(patch)
    except ValidationError as error:
        return PatchResult(
            graph,
            tuple(
                copy.replace(issue("invalid-patch", item["msg"]), path=item["loc"])
                for item in error.errors()
            ),
        )

    draft = graph.draft()
    editor = _Editor(draft, codecs, threshold)
    editor.apply(parsed)

    if has_errors(editor.issues):
        return PatchResult(graph, tuple(editor.issues))

    created: list[str] = []
    updated: list[str] = []
    removed: list[str] = []

    for before, after, items in (
        (graph.atom_nodes, draft.atom_nodes, parsed.atoms),
        (graph.scheme_nodes, draft.scheme_nodes, parsed.schemes),
        (graph.resources, draft.resources, parsed.resources),
        (graph.participants, draft.participants, parsed.participants),
    ):
        submitted = {item.id for item in items}
        created.extend(id for id in after if id not in before)
        updated.extend(id for id in after if id in before and id in submitted)
        removed.extend(id for id in before if id not in after)

    return PatchResult(
        draft.freeze(),
        tuple(editor.issues),
        tuple(created),
        tuple(updated),
        tuple(removed),
    )
