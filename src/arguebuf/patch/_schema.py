from collections.abc import Mapping, Sequence
from typing import Final, Literal, NotRequired, Required, TypedDict

from arguebuf.model.scheme import SchemeType, name2scheme_type

__all__ = (
    "PARTICIPANT_FIELDS",
    "PATCH_SCHEMA",
    "AtomPatch",
    "JsonSchema",
    "Outline",
    "ParticipantPatch",
    "Patch",
    "Path",
    "ResourcePatch",
    "SchemePatch",
)


class ResourcePatch(TypedDict, total=False):
    """Resource of a patch."""

    id: Required[str]
    text: str
    title: str | None
    source: str | None


class ParticipantPatch(TypedDict, total=False):
    """Participant of a patch."""

    id: Required[str]
    name: str | None
    username: str | None
    email: str | None
    url: str | None
    location: str | None
    description: str | None


class AtomPatch(TypedDict, total=False):
    """Atom node of a patch.

    `resource` is the resource the text is quoted from,
    None removes the reference and all resources are searched by default.
    """

    id: Required[str]
    text: str
    resource: str | None
    participant: str | None


class SchemePatch(TypedDict, total=False):
    """Scheme node of a patch, `scheme` is a label of the type, e.g. "Expert Opinion"."""

    id: Required[str]
    type: SchemeType
    scheme: str
    premises: Sequence[str]
    conclusion: str


# the field names match the JSON of all arguebuf implementations
Patch = TypedDict(
    "Patch",
    {
        "clear": NotRequired[bool],
        "remove": NotRequired[Sequence[str]],
        "resources": NotRequired[Sequence[ResourcePatch]],
        "participants": NotRequired[Sequence[ParticipantPatch]],
        "atoms": NotRequired[Sequence[AtomPatch]],
        "schemes": NotRequired[Sequence[SchemePatch]],
        "majorClaim": NotRequired[str | None],
    },
)
"""Changes to a graph referencing elements by id.

An item creates the element if its id is new and otherwise updates the given fields,
None clears a field.
The changes are applied in the order of the fields.
`remove` takes ids of nodes, resources, or participants,
schemes left without premise or conclusion are removed as well (see `Graph.remove_node`).
"""

Outline = TypedDict(
    "Outline",
    {
        "resources": list[ResourcePatch],
        "participants": list[ParticipantPatch],
        "atoms": list[AtomPatch],
        "schemes": list[SchemePatch],
        "majorClaim": NotRequired[str],
    },
)
"""Graph in the shape of a patch, without the texts of resources and without None values."""

type _SchemaValue = (
    str | int | float | bool | None | Sequence[_SchemaValue] | Mapping[str, _SchemaValue]
)
type JsonSchema = Mapping[str, _SchemaValue]

_NULLABLE: Final[JsonSchema] = {"type": ["string", "null"]}

PARTICIPANT_FIELDS: Final[
    tuple[Literal["name", "username", "email", "url", "location", "description"], ...]
] = ("name", "username", "email", "url", "location", "description")


def _items_schema(description: str, properties: dict[str, JsonSchema]) -> JsonSchema:
    return {
        "type": "array",
        "description": description,
        "items": {
            "type": "object",
            "properties": {"id": {"type": "string"}, **properties},
            "required": ["id"],
            "additionalProperties": False,
        },
    }


PATCH_SCHEMA: Final[JsonSchema] = {
    "type": "object",
    "description": "Changes to an argument graph, applied all or nothing. An item creates the element if its id is new and otherwise updates the given fields, null clears a field.",
    "properties": {
        "clear": {
            "type": "boolean",
            "description": "Remove all atoms and schemes first.",
        },
        "remove": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Ids of atoms, schemes, resources, or participants. Schemes left without premise or conclusion are removed as well.",
        },
        "resources": _items_schema(
            "Source documents.",
            {"text": {"type": "string"}, "title": _NULLABLE, "source": _NULLABLE},
        ),
        "participants": _items_schema(
            "People making the statements.",
            dict.fromkeys(PARTICIPANT_FIELDS, _NULLABLE),
        ),
        "atoms": _items_schema(
            "Claims and premises.",
            {
                "text": {
                    "type": "string",
                    "description": "Quote it verbatim from a resource.",
                },
                "resource": {
                    "type": ["string", "null"],
                    "description": "Id of the resource the text is quoted from, all are searched by default.",
                },
                "participant": _NULLABLE,
            },
        ),
        "schemes": _items_schema(
            "Relations from premises to a conclusion.",
            {
                "type": {"type": "string", "enum": list(name2scheme_type)},
                "scheme": {
                    "type": "string",
                    "description": "Argumentation scheme, e.g. Expert Opinion.",
                },
                "premises": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "description": "Ids of atoms.",
                },
                "conclusion": {
                    "type": "string",
                    "description": "Id of an atom or of a scheme to undercut.",
                },
            },
        ),
        "majorClaim": {
            "type": ["string", "null"],
            "description": "Id of the atom the argument is about.",
        },
    },
    "additionalProperties": False,
}
"""JSON Schema of `Patch`, e.g. for the tools of agents."""


type Path = tuple[str | int, ...]
"""Location in the input, e.g. `("schemes", 2, "premises")`."""
