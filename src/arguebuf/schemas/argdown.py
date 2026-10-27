"""Subset of the Argdown JSON export (https://argdown.org) read by the loader."""

import typing as t

from arguebuf.model.userdata import JsonObject, JsonValue

__all__ = (
    "Argument",
    "EquivalenceClass",
    "Graph",
    "Inference",
    "MemberType",
    "Relation",
    "RelationType",
    "Statement",
)

type MemberType = t.Literal["equivalence-class", "argument", "inference"]
type RelationType = t.Literal[
    "support", "entails", "attack", "undercut", "contrary", "contradictory"
]


class Inference(t.TypedDict):
    inferenceRules: t.NotRequired[t.ReadOnly[list[JsonValue]]]
    data: t.NotRequired[t.ReadOnly[JsonObject]]


class Statement(t.TypedDict):
    title: t.NotRequired[t.ReadOnly[str]]
    text: t.NotRequired[t.ReadOnly[str]]
    role: t.NotRequired[t.ReadOnly[str]]
    isReference: t.NotRequired[t.ReadOnly[bool]]
    data: t.NotRequired[t.ReadOnly[JsonObject]]
    inference: t.NotRequired[t.ReadOnly[Inference]]


class EquivalenceClass(t.TypedDict):
    title: t.ReadOnly[str]
    members: t.ReadOnly[list[Statement]]
    tags: t.NotRequired[t.ReadOnly[list[JsonValue]]]
    data: t.NotRequired[t.ReadOnly[JsonObject]]


class Argument(t.TypedDict):
    title: t.ReadOnly[str]
    members: t.ReadOnly[list[Statement]]
    pcs: t.ReadOnly[list[Statement]]
    tags: t.NotRequired[t.ReadOnly[list[JsonValue]]]
    data: t.NotRequired[t.ReadOnly[JsonObject]]


# Members are referenced by title, inferences by argument title and `conclusionIndex`.
# `from` is a keyword and thus requires the functional syntax.
Relation = t.TypedDict(
    "Relation",
    {
        "relationType": t.ReadOnly[RelationType],
        "from": t.ReadOnly[str],
        "fromType": t.ReadOnly[MemberType],
        "to": t.ReadOnly[str],
        "toType": t.ReadOnly[MemberType],
        "conclusionIndex": t.NotRequired[t.ReadOnly[int]],
    },
)


class Graph(t.TypedDict):
    statements: t.ReadOnly[dict[str, EquivalenceClass]]
    arguments: t.ReadOnly[dict[str, Argument]]
    relations: t.ReadOnly[list[Relation]]
    # not part of the upstream export, added by arguebuf-typescript's `loadArgdown`
    frontMatter: t.NotRequired[t.ReadOnly[JsonObject]]
