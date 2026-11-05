import copy
from collections.abc import Callable, Mapping
from collections.abc import Set as AbstractSet
from dataclasses import dataclass, field

from arguebuf.locate import DEFAULT_THRESHOLD
from arguebuf.model import Graph, GraphDraft
from arguebuf.model.edge import Edge
from arguebuf.model.issue import Issue, catch_graph_error, fail, has_errors
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.reference import Reference
from arguebuf.model.resource import Resource
from arguebuf.model.scheme import Scheme
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs
from arguebuf.patch._resolve import link_text, resolve_scheme_of
from arguebuf.patch._schema import (
    AtomPatch,
    ParticipantPatch,
    Patch,
    Path,
    ResourcePatch,
    SchemePatch,
)

__all__ = ("PatchResult", "apply_patch")


@dataclass(slots=True, frozen=True)
class PatchResult[A, S, E, R, P, N, G]:
    """Result of `apply_patch`.

    The ids cover nodes, resources, and participants and are empty if there are errors.

    Attributes:
        graph: The changed graph, or the input if there are errors.
        issues: Errors and warnings, each pointing to its item via `path`.
        created: Ids of the new elements.
        updated: Ids of the existing elements that the patch changed.
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
    # ids of the nodes, resources, and participants of the input,
    # which may be removed by cascades before `remove` names them
    initial: AbstractSet[str]
    issues: list[Issue] = field(default_factory=list)

    def apply(self, patch: Patch) -> None:
        graph = self.graph

        if patch.get("clear"):
            graph.remove_elements(list(graph.nodes))

        for index, id in enumerate(patch.get("remove", ())):
            self._attempt(("remove", index), lambda id=id: self._remove(id))

        for index, resource in enumerate(patch.get("resources", ())):
            self._attempt(
                ("resources", index), lambda item=resource: self._resource(item)
            )

        for index, participant in enumerate(patch.get("participants", ())):
            self._attempt(
                ("participants", index),
                lambda item=participant: self._participant(item),
            )

        for index, atom in enumerate(patch.get("atoms", ())):
            path = ("atoms", index)
            self._attempt(path, lambda item=atom, path=path: self._atom(item, path))

        # all schemes exist before they are wired, so that schemes can target schemes
        schemes = patch.get("schemes", ())
        created = [
            self._attempt(
                ("schemes", index),
                lambda item=item, index=index: self._scheme(item, ("schemes", index)),
            )
            for index, item in enumerate(schemes)
        ]

        for index, (item, ok) in enumerate(zip(schemes, created, strict=True)):
            if ok:
                self._attempt(("schemes", index), lambda item=item: self._wire(item))

        if "majorClaim" in patch:
            self._attempt(("majorClaim",), lambda: self._major_claim(patch))

    def _attempt(self, path: Path, action: Callable[[], None]) -> bool:
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

    def _link(self, source: str, target: str) -> None:
        self.graph.add_edge(
            Edge(source, target, userdata=self.codecs.edge.validate_python({}))
        )

    def _remove(self, id: str) -> None:
        graph = self.graph
        present = id in graph.nodes or id in graph.resources or id in graph.participants

        # skip elements already removed by a cascade or an earlier item
        if present or id not in self.initial:
            graph.remove_elements([id])

    def _resource(self, item: ResourcePatch) -> None:
        graph = self.graph
        id = item["id"]

        if id not in graph.resources:
            if "text" not in item:
                fail("invalid-patch", f"The new resource '{id}' needs a text.", [id])

            graph.add_resource(
                Resource(
                    item["text"],
                    title=item.get("title"),
                    source=item.get("source"),
                    userdata=self.codecs.resource.validate_python({}),
                    id=id,
                )
            )

            return

        resource = graph.resources[id]
        self.issues.extend(
            graph.update_resource(
                id,
                threshold=self.threshold,
                text=item.get("text", resource.text),
                title=item.get("title", resource.title),
                source=item.get("source", resource.source),
            )
        )

    def _participant(self, item: ParticipantPatch) -> None:
        graph = self.graph
        id = item["id"]
        current = graph.participants.get(id)

        if current is None:
            current = Participant(
                userdata=self.codecs.participant.validate_python({}), id=id
            )
            graph.add_participant(current)

        graph.update_participant(
            id,
            name=item.get("name", current.name),
            username=item.get("username", current.username),
            email=item.get("email", current.email),
            url=item.get("url", current.url),
            location=item.get("location", current.location),
            description=item.get("description", current.description),
        )

    def _atom(self, item: AtomPatch, path: Path) -> None:
        graph = self.graph
        id = item["id"]
        atom = self._find(id, graph.atom_nodes)
        participant = item.get("participant")

        if participant is not None and participant not in graph.participants:
            fail(
                "unknown-element",
                f"Participant '{participant}' does not exist.",
                [participant],
            )

        unlinked = "resource" in item and item["resource"] is None

        if atom is None:
            if "text" not in item:
                fail("invalid-patch", f"The new atom '{id}' needs a text.", [id])

            text = item["text"]
            graph.add_node(
                AtomNode(
                    text,
                    participant=participant,
                    reference=None
                    if unlinked
                    else self._reference(path, id, text, item.get("resource")),
                    userdata=self.codecs.atom.validate_python({}),
                    id=id,
                )
            )

            return

        text = item.get("text", atom.text)
        reference = atom.reference

        if "text" in item or "resource" in item:
            scope = (
                item.get("resource")
                if "resource" in item
                else (atom.reference.resource if atom.reference else None)
            )
            reference = None if unlinked else self._reference(path, id, text, scope)

        graph.update_atom(
            atom,
            text=text,
            reference=reference,
            participant=participant if "participant" in item else atom.participant,
        )

    def _reference(
        self, path: Path, id: str, text: str, scope: str | None
    ) -> Reference | None:
        """Link the text, reporting why it is not linked or only to a similar span."""
        link = link_text(self.graph.resources, id, text, scope, self.threshold)
        self._warn(path, link.warning)

        return link.reference

    def _scheme_of(
        self, item: SchemePatch, current: type[Scheme] | None, path: Path
    ) -> Scheme:
        resolved = resolve_scheme_of(item, current)
        self._warn(path, resolved.warning)

        return resolved.scheme

    def _scheme(self, item: SchemePatch, path: Path) -> None:
        """Create or retype the scheme node, it is wired afterwards."""
        graph = self.graph
        id = item["id"]
        scheme = self._find(id, graph.scheme_nodes)

        if scheme is None:
            if "premises" not in item or "conclusion" not in item:
                fail(
                    "invalid-patch",
                    f"The new scheme '{id}' needs premises and a conclusion.",
                    [id],
                )

            graph.add_node(
                SchemeNode(
                    self._scheme_of(item, None, path),
                    userdata=self.codecs.scheme.validate_python({}),
                    id=id,
                )
            )
        elif "type" in item or "scheme" in item:
            current = type(scheme.scheme) if scheme.scheme is not None else None
            graph.update_scheme(scheme, scheme=self._scheme_of(item, current, path))

    def _wire(self, item: SchemePatch) -> None:
        """Replace the premises and the conclusion that the item specifies.

        Premises are atoms, schemes targeting this scheme (e.g. undercutters) are kept.
        """
        graph = self.graph
        id = item["id"]
        premises = item.get("premises")
        conclusion = item.get("conclusion")
        sources = (
            list(premises)
            if premises is not None
            else [node.id for node in graph.premise_nodes(id)]
        )

        if premises is not None and not premises:
            fail("invalid-patch", f"Scheme '{id}' needs at least one premise.", [id])

        for premise in premises or ():
            if self._find(premise, graph.atom_nodes) is None:
                fail(
                    "unknown-element",
                    f"Premise '{premise}' of scheme '{id}' does not exist.",
                    [id, premise],
                )

        if conclusion is not None and conclusion not in graph.nodes:
            fail(
                "unknown-element",
                f"Conclusion '{conclusion}' of scheme '{id}' does not exist.",
                [id, conclusion],
            )

        if conclusion is not None and conclusion in sources:
            fail(
                "invalid-patch",
                f"Scheme '{id}' uses its conclusion '{conclusion}' as premise.",
                [id, conclusion],
            )

        if premises is not None:
            for edge in list(graph.incoming_edges(id)):
                if edge.source in graph.atom_nodes:
                    graph.remove_edge(edge)

            for premise in premises:
                self._link(premise, id)

        if conclusion is not None:
            for edge in list(graph.outgoing_edges(id)):
                graph.remove_edge(edge)

            self._link(id, conclusion)

    def _major_claim(self, patch: Patch) -> None:
        self.graph.major_claim = patch.get("majorClaim")


def apply_patch[A, S, E, R, P, N, G](
    graph: Graph[A, S, E, R, P, N, G],
    patch: Patch,
    *,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    threshold: float = DEFAULT_THRESHOLD,
) -> PatchResult[A, S, E, R, P, N, G]:
    """Apply a patch to a graph, all or nothing.

    The patch is applied to a draft of the graph (see `Graph.draft`),
    so the result shares the unchanged elements with the input.
    Texts of atoms are linked to the most similar spans of the resources (see `locate`).
    Validate untrusted input with `parse_patch` first.

    Args:
        graph: Graph to apply the patch to.
        patch: Changes referencing elements by id.
        codecs: Codecs creating the userdata of new elements.
        threshold: Minimal similarity of the spans linked to atoms.

    Returns:
        The changed graph, the issues, and the ids of the changed elements,
        or the input graph if an issue is an error.

    Examples:
        >>> result = apply_patch(Graph(), {"atoms": [{"id": "a", "text": "Claim"}], "majorClaim": "a"})
        >>> result.graph.major_claim, result.issues, result.created
        ('a', (), ('a',))
    """
    draft = graph.draft()
    initial = graph.nodes.keys() | graph.resources.keys() | graph.participants.keys()
    editor = _Editor(draft, codecs, threshold, initial)
    editor.apply(patch)

    if has_errors(editor.issues):
        return PatchResult(graph, tuple(editor.issues))

    stores = (
        (graph.nodes, draft.nodes),
        (graph.resources, draft.resources),
        (graph.participants, draft.participants),
    )
    named = {
        item["id"]
        for key in ("resources", "participants", "atoms", "schemes")
        for item in patch.get(key, ())
    }

    return PatchResult(
        draft.freeze(),
        tuple(editor.issues),
        created=tuple(
            id for before, after in stores for id in after if id not in before
        ),
        updated=tuple(
            id
            for before, after in stores
            for id in after
            if id in before and id in named
        ),
        removed=tuple(
            id for before, after in stores for id in before if id not in after
        ),
    )
