"""Subset of the Argdown JSON export (https://argdown.org) read by arguebuf."""

import typing as t

from arguebuf.model.userdata import JsonObject

__all__ = (
    "Argument",
    "EquivalenceClass",
    "Graph",
    "Inference",
    "Member",
    "Relation",
    "Statement",
)


class Inference(t.TypedDict):
    """Inference of a conclusion."""

    inferenceRules: t.NotRequired[list[str] | None]
    data: t.NotRequired[JsonObject | None]


class Member(t.TypedDict):
    """Statement that is a member of an equivalence class or an argument.

    Any truthy `isReference` marks a reference.
    """

    text: t.NotRequired[str | None]
    isReference: t.NotRequired[object]
    data: t.NotRequired[JsonObject | None]


class Statement(t.TypedDict):
    """Statement of a premise conclusion structure, a conclusion has an inference."""

    title: str
    role: t.NotRequired[str | None]
    data: t.NotRequired[JsonObject | None]
    inference: t.NotRequired[Inference | None]


class EquivalenceClass(t.TypedDict):
    """Statement defined by its members."""

    title: str
    members: list[Member]
    tags: t.NotRequired[list[str] | None]
    data: t.NotRequired[JsonObject | None]


class Argument(t.TypedDict):
    """Argument, reconstructed if it has premise conclusion statements (`pcs`)."""

    title: str
    members: list[Member]
    pcs: list[Statement]
    tags: t.NotRequired[list[str] | None]
    data: t.NotRequired[JsonObject | None]


# `from` is a keyword and thus requires the functional syntax
Relation = t.TypedDict(
    "Relation",
    {
        "relationType": str,
        "from": str,
        "fromType": str,
        "to": str,
        "toType": str,
        "conclusionIndex": t.NotRequired[int | None],
    },
)
"""Relation between members of the types `equivalence-class`, `argument`, or `inference`.

Members are referenced by title, inferences by argument title and `conclusionIndex`.
The loader skips unknown relation and member types.
"""


class Graph(t.TypedDict):
    """Argdown JSON export.

    The `frontMatter` is not part of the upstream export,
    it is added by arguebuf-typescript's `loadArgdown`.
    """

    statements: dict[str, EquivalenceClass]
    arguments: dict[str, Argument]
    relations: list[Relation]
    frontMatter: t.NotRequired[JsonObject | None]
