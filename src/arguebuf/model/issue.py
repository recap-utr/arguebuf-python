"""Issues describing problems of graphs and inputs, shared by all arguebuf implementations."""

import logging
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from typing import Final, Literal, NoReturn, TypeIs, get_args

__all__ = (
    "ISSUE_CODES",
    "GraphError",
    "Issue",
    "IssueCode",
    "Reporter",
    "Severity",
    "catch_graph_error",
    "has_errors",
    "is_issue_code",
    "issue",
    "unresolved_reference",
)

type IssueCode = Literal[
    "duplicate-id",
    "unknown-element",
    "invalid-major-claim",
    "self-loop",
    "atom-edge",
    "parallel-edge",
    "invalid-patch",
    "invalid-input",
    "unknown-scheme",
    "untyped-scheme",
    "reference-mismatch",
    "reference-unresolved",
    "orphaned-atom",
    "scheme-without-premise",
    "scheme-without-conclusion",
    "scheme-multiple-conclusions",
    "scheme-multiple-premises",
    "circular-scheme",
    "disconnected",
    "no-major-claim",
    "unreachable-major-claim",
]
"""Stable identifiers of issues, identical in all arguebuf implementations."""

ISSUE_CODES: Final[tuple[IssueCode, ...]] = get_args(IssueCode.__value__)
"""All issue codes."""


def is_issue_code(value: str) -> TypeIs[IssueCode]:
    """Whether the string is an issue code, e.g. given on the command line."""
    return value in ISSUE_CODES


type Severity = Literal["error", "warning"]

type JsonIssue = dict[str, str | list[str] | list[str | int]]

_ERRORS: Final[frozenset[IssueCode]] = frozenset(
    (
        "duplicate-id",
        "unknown-element",
        "invalid-major-claim",
        "self-loop",
        "atom-edge",
        "parallel-edge",
        "invalid-patch",
        "invalid-input",
        "untyped-scheme",
    )
)

_HINTS: Final[dict[IssueCode, str]] = {
    "duplicate-id": "Use an id that is not taken.",
    "unknown-element": "Reference an existing element or create it first.",
    "invalid-major-claim": "Choose an atom as major claim.",
    "self-loop": "Connect the node to another node.",
    "atom-edge": "Connect atoms through a scheme node.",
    "parallel-edge": "Remove the duplicate connection.",
    "invalid-input": "Check the input against the specification of its format.",
    "untyped-scheme": "Set the type to support, attack, rephrase, or preference.",
    "unknown-scheme": "Use a scheme of the type, e.g. Expert Opinion, or omit it.",
    "reference-mismatch": "Quote the source text verbatim.",
    "reference-unresolved": "Quote the source text verbatim.",
    "orphaned-atom": "Connect the atom through a scheme node or remove it.",
    "scheme-without-premise": "Add a premise or remove the scheme.",
    "scheme-without-conclusion": "Add a conclusion or remove the scheme.",
    "scheme-multiple-conclusions": "Split the scheme so that each one has a single conclusion.",
    "scheme-multiple-premises": "Split the scheme so that each one has a single premise, only supports can have several.",
    "circular-scheme": "Use different nodes as premise and conclusion.",
    "disconnected": "Connect the parts into a single argument.",
    "no-major-claim": "Set the atom that the argument is about as major claim.",
    "unreachable-major-claim": "Connect the atom to the major claim, directly or indirectly.",
}


@dataclass(slots=True, frozen=True)
class Issue:
    """Problem of a graph or of an input.

    Errors prevent an operation, warnings describe a repair or a quality problem.

    Attributes:
        code: Stable identifier, identical in all arguebuf implementations.
        severity: Whether the issue is an error or a warning.
        message: Complete sentence naming the affected elements.
        hint: Imperative remediation for humans and agents.
        elements: Ids of the affected elements.
        path: Location in the input, e.g. `("schemes", 2, "premises")`.
    """

    code: IssueCode
    severity: Severity
    message: str
    hint: str | None = None
    elements: tuple[str, ...] = ()
    path: tuple[str | int, ...] | None = None

    def to_dict(self) -> JsonIssue:
        """Convert the issue to the JSON object of all arguebuf implementations.

        Examples:
            >>> issue("self-loop", "Node 'n' cannot be connected to itself.").to_dict()["hint"]
            'Connect the node to another node.'
        """
        return {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in asdict(self).items()
            if value is not None
        }


type Reporter = Callable[[Issue], None]
"""Receives the issues of loaders and other lenient operations."""


def issue(
    code: IssueCode,
    message: str,
    elements: Iterable[str] = (),
    *,
    severity: Severity | None = None,
) -> Issue:
    """Create an issue with the default severity and hint of its code.

    Examples:
        >>> issue("orphaned-atom", "Atom 'a' has no relations.").severity
        'warning'
    """
    return Issue(
        code,
        severity or ("error" if code in _ERRORS else "warning"),
        message,
        _HINTS.get(code),
        tuple(elements),
    )


def has_errors(issues: Iterable[Issue]) -> bool:
    """Check whether any of the issues is an error."""
    return any(item.severity == "error" for item in issues)


class GraphError(ValueError):
    """Error raised by the strict model, its `issue` describes the cause."""

    issue: Issue

    def __init__(self, issue: Issue) -> None:
        super().__init__(issue.message)
        self.issue = issue


def catch_graph_error(action: Callable[[], object]) -> Issue | None:
    """Run the action and return the issue of its `GraphError`, other errors are raised.

    Examples:
        >>> catch_graph_error(lambda: fail("self-loop", "Loop.")).code
        'self-loop'
        >>> catch_graph_error(lambda: None) is None
        True
    """
    try:
        action()
    except GraphError as error:
        return error.issue

    return None


def unresolved_reference(atom_id: str, resource_id: str) -> Issue:
    """The reference of the atom is not found in its resource."""
    return issue(
        "reference-unresolved",
        f"The reference of atom '{atom_id}' is not found in resource '{resource_id}'.",
        (atom_id, resource_id),
    )


def fail(code: IssueCode, message: str, elements: Iterable[str] = ()) -> NoReturn:
    """Raise a `GraphError` with the issue of the given code."""
    raise GraphError(issue(code, message, elements))


_log = logging.getLogger("arguebuf")


def warn(item: Issue) -> None:
    """Default reporter of loaders, logs the issue as warning."""
    _log.warning(item.message)
