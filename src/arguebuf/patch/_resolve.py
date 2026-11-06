"""Fields of patch items resolved to the values of the model, with a warning about the result."""

from collections.abc import Mapping
from dataclasses import dataclass

from arguebuf.locate import Match, locate
from arguebuf.model.issue import Issue, fail, issue
from arguebuf.model.reference import Reference
from arguebuf.model.resource import Resource
from arguebuf.model.scheme import (
    SCHEME_TYPE_NAMES,
    Scheme,
    is_default_scheme,
    normalize_scheme_label,
    resolve_scheme,
)

__all__ = ("Link", "ResolvedScheme", "link_text", "resolve_scheme_of")


@dataclass(slots=True, frozen=True)
class Link:
    """Reference of an atom and why its text is not linked or only to a similar span."""

    reference: Reference | None = None
    warning: Issue | None = None


@dataclass(slots=True, frozen=True)
class ResolvedScheme:
    """Scheme of a scheme node and why the default is used instead of the given one."""

    scheme: Scheme
    warning: Issue | None = None


def link_text[R](
    resources: Mapping[str, Resource[R]],
    id: str,
    text: str,
    scope: str | None,
    threshold: float,
) -> Link:
    """Link the text of the atom `id` to the most similar span of the resource `scope`.

    All resources are searched if `scope` is None.
    """
    if scope is not None and scope not in resources:
        fail("unknown-element", f"Resource '{scope}' does not exist.", [scope])

    candidates = list(resources.values()) if scope is None else [resources[scope]]
    best: tuple[Match, Resource[R]] | None = None

    for candidate in candidates:
        match = locate(candidate.text, text, threshold=threshold)

        if match and match.similarity > (best[0].similarity if best else 0):
            best = (match, candidate)

    if best is None:
        if not candidates:
            return Link()

        where = "any resource" if scope is None else f"resource '{scope}'"

        return Link(
            warning=issue(
                "reference-unresolved",
                f"The text of atom '{id}' is not found in {where}, so it is not linked.",
                [id],
            )
        )

    match, resource = best
    reference = Reference(match.text, resource=resource.id, offset=match.offset)

    if match.similarity < 1:
        return Link(
            reference,
            issue(
                "reference-mismatch",
                f"Atom '{id}' is linked to the similar text '{match.text}' of resource '{resource.id}'.",
                [id, resource.id],
            ),
        )

    return Link(reference)


def resolve_scheme_of(
    id: str, scheme_type: type[Scheme], label: str | None
) -> ResolvedScheme:
    """The scheme of the type with the label of the scheme `id`, the default without a label."""
    if label is None:
        return ResolvedScheme(scheme_type.DEFAULT)

    scheme = resolve_scheme(scheme_type, label)

    if is_default_scheme(scheme) and normalize_scheme_label(label) != "default":
        return ResolvedScheme(
            scheme,
            issue(
                "unknown-scheme",
                f"The {SCHEME_TYPE_NAMES[scheme_type]} scheme '{label}' of '{id}' is unknown, the default is used.",
                [id],
            ),
        )

    return ResolvedScheme(scheme)
