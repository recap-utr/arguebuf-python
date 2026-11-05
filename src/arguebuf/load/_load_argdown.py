import json
from collections.abc import Mapping, Sequence
from types import MappingProxyType
from typing import Final

from arguebuf.model import Graph, GraphDraft
from arguebuf.model.issue import Reporter
from arguebuf.model.node import AtomNode, AtomOrSchemeNode, SchemeNode
from arguebuf.model.scheme import Attack, Scheme, Support
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject, JsonValue
from arguebuf.model.utils import uuid
from arguebuf.schemas import argdown

from ._helpers import Context, add_edge, compact, connect, lookup

__all__ = ("load_argdown",)

# scheme of a relation and whether it also applies in the opposite direction
_RELATION_SCHEMES: Final[Mapping[argdown.RelationType, tuple[Scheme, bool]]] = (
    MappingProxyType(
        {
            "support": (Support.DEFAULT, False),
            "entails": (Support.DEFAULT, False),
            "attack": (Attack.DEFAULT, False),
            "undercut": (Attack.DEFAULT, False),
            "contrary": (Attack.DEFAULT, True),
            "contradictory": (Attack.DEFAULT, True),
        }
    )
)


def _userdata(**fields: JsonValue) -> JsonObject:
    return {"argdown": compact(fields)}


def _canonical_text(members: Sequence[argdown.Statement]) -> str | None:
    """Text of the last defining member, preferring members marked as canonical (upstream rule)."""
    definitions = [member for member in members if not member.get("isReference")]
    canonical = [
        member
        for member in definitions
        if member.get("data", {}).get("isCanonical") is True
    ]

    if (candidates := canonical or definitions) and (
        text := candidates[-1].get("text")
    ) is not None:
        return text.strip()

    return None


def _is_conclusion(statement: argdown.Statement) -> bool:
    return "inference" in statement and statement.get("role") in (
        "intermediary-conclusion",
        "main-conclusion",
    )


def _premises(argument: argdown.Argument, index: int) -> list[argdown.Statement]:
    """Premises of the conclusion at `index`, its `uses` or all statements back to the previous conclusion."""
    pcs = argument["pcs"]
    conclusion = pcs[index]
    uses = conclusion.get("inference", {}).get("data", {}).get("uses")

    if uses is None:
        uses = conclusion.get("data", {}).get("uses")

    if uses is None:
        start = index - 1

        while start > 0 and not _is_conclusion(pcs[start]):
            start -= 1

        return pcs[max(start, 0) : index]

    if not isinstance(uses, list) or not all(
        type(n) is int and 1 <= n <= index for n in uses
    ):
        raise ValueError(
            f"Invalid 'uses' {json.dumps(uses)} of statement {index + 1} in argument '{argument['title']}'."
        )

    # the filter only narrows the type of the validated numbers
    return [pcs[n - 1] for n in uses if type(n) is int]


def load_argdown[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    obj: argdown.Graph,
    *,
    name: str | None = None,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, R, P, N, G]:
    """Generate a graph from the Argdown JSON export (https://argdown.org).

    Equivalence classes and unreconstructed arguments become atom nodes,
    inferences of reconstructed arguments and relations become scheme nodes.
    Reconstructed arguments are represented by their main inference.

    Raises:
        ValueError: If an inference `uses` invalid statement numbers.
    """
    g: GraphDraft[A, S, E, R, P, N, G] = GraphDraft(
        name, userdata=codecs.graph.validate_python(obj.get("frontMatter") or {})
    )
    ctx = Context(codecs, on_issue, strict)
    # inference scheme nodes by argument title and conclusion index
    inferences: dict[str, dict[int, SchemeNode[S]]] = {}

    def add_atom(
        element: argdown.EquivalenceClass | argdown.Argument, **fields: JsonValue
    ) -> AtomNode[A]:
        node = AtomNode(
            _canonical_text(element["members"]) or element["title"],
            userdata=codecs.atom.validate_python(
                _userdata(
                    title=element["title"],
                    tags=element.get("tags"),
                    data=element.get("data"),
                    **fields,
                )
            ),
        )
        g.add_node(node)

        return node

    statements = {title: add_atom(ec) for title, ec in obj["statements"].items()}

    def add_inferences(title: str, argument: argdown.Argument) -> SchemeNode[S] | None:
        main = None
        owner = f"argument '{title}'"

        for index, statement in enumerate(argument["pcs"]):
            if not _is_conclusion(statement):
                continue

            inference = statement.get("inference", {})
            scheme = SchemeNode(
                Support.DEFAULT,
                userdata=codecs.scheme.validate_python(
                    _userdata(
                        title=title,
                        description=_canonical_text(argument["members"]),
                        inferenceRules=inference.get("inferenceRules"),
                        data=inference.get("data"),
                    )
                ),
            )
            g.add_node(scheme)

            for premise in _premises(argument, index):
                if node := lookup(
                    ctx, statements, premise.get("title"), "equivalence-class", owner
                ):
                    add_edge(g, ctx, node.id, scheme.id, uuid())

            if conclusion := lookup(
                ctx, statements, statement.get("title"), "equivalence-class", owner
            ):
                add_edge(g, ctx, scheme.id, conclusion.id, uuid())

            inferences.setdefault(title, {})[index] = scheme
            main = scheme

        return main

    arguments = {
        title: add_inferences(title, argument) or add_atom(argument, argument=True)
        for title, argument in obj["arguments"].items()
    }
    members: dict[argdown.MemberType, Mapping[str, AtomOrSchemeNode[A, S]]] = {
        "equivalence-class": statements,
        "argument": arguments,
    }

    def member(
        title: str, type: argdown.MemberType, index: int | None, owner: str
    ) -> AtomOrSchemeNode[A, S] | None:
        if type != "inference":
            return lookup(ctx, members.get(type, {}), title, type, owner)

        nodes = inferences.get(title, {})

        if index is None or (node := nodes.get(index)) is None:
            ctx.report(
                "unknown-element",
                f"Skipping unknown inference {index} of argument '{title}' referenced by {owner}.",
                [title],
            )

            return None

        return node

    for relation in obj["relations"]:
        relation_type = relation["relationType"]
        owner = f"{relation_type} relation"

        if (
            mapping := lookup(
                ctx, _RELATION_SCHEMES, relation_type, "relation type", owner
            )
        ) is None:
            continue

        scheme, symmetric = mapping
        source = member(relation["from"], relation["fromType"], None, owner)
        target = member(
            relation["to"], relation["toType"], relation.get("conclusionIndex"), owner
        )

        if source is None or target is None:
            continue

        directions = [(source, target)]

        if symmetric:
            directions.append((target, source))

        for start, end in directions:
            scheme_node = SchemeNode(
                scheme,
                userdata=codecs.scheme.validate_python(
                    _userdata(relationType=relation_type)
                ),
            )
            g.add_node(scheme_node)
            connect(g, ctx, [start.id], scheme_node.id, end.id)

    return g.freeze()
