from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from arguebuf.model.scheme import SchemeType

__all__ = (
    "AtomPatch",
    "Outline",
    "ParticipantPatch",
    "Patch",
    "ResourceOutline",
    "ResourcePatch",
    "SchemeOutline",
    "SchemePatch",
)


class _Model(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        validate_by_name=True,
        serialize_by_alias=True,
        alias_generator=to_camel,
    )


class ResourcePatch(_Model):
    """Source document."""

    id: str
    text: str
    title: str | None = None
    source: str | None = None


class ParticipantPatch(_Model):
    """Person making statements."""

    id: str
    name: str | None = None
    username: str | None = None
    email: str | None = None
    url: str | None = None
    location: str | None = None
    description: str | None = None


class AtomPatch(_Model):
    """Claim or premise."""

    id: str
    text: str = Field(description="Quote it verbatim from a resource.")
    resource: str | None = Field(
        default=None,
        description="Id of the resource the text is quoted from, all resources are searched if omitted.",
    )
    participant: str | None = Field(default=None, description="Id of the participant.")


class SchemePatch(_Model):
    """Relation from premises to a conclusion."""

    id: str
    type: SchemeType
    scheme: str | None = Field(
        default=None,
        description="Argumentation scheme of the type, e.g. Expert Opinion.",
    )
    premises: tuple[str, ...] = Field(
        min_length=1, description="Ids of atoms, only supports take several."
    )
    conclusion: str = Field(description="Id of an atom or of a scheme.")


class Patch(_Model):
    """Changes to an argument graph, applied all or nothing in the order of the fields. An item with a new id of your choice creates the element, an item with an existing id replaces it with all given fields.

    Examples:
        >>> Patch.model_validate({"majorClaim": "a"}).major_claim
        'a'
    """

    clear: bool = Field(
        default=False,
        description="Remove all atoms and schemes first, resources and participants are kept.",
    )
    delete: tuple[str, ...] = Field(
        default=(),
        description="Ids of atoms, schemes, resources, or participants to remove. Schemes left without premise or conclusion are removed as well.",
    )
    resources: tuple[ResourcePatch, ...] = ()
    participants: tuple[ParticipantPatch, ...] = ()
    atoms: tuple[AtomPatch, ...] = ()
    schemes: tuple[SchemePatch, ...] = ()
    major_claim: str | None = Field(
        default=None,
        description="Id of the atom the argument is about, the current one is kept if omitted.",
    )


class ResourceOutline(_Model):
    """Resource of an outline, without its text."""

    id: str
    title: str | None = None
    source: str | None = None


class SchemeOutline(_Model):
    """Scheme node of an outline, which may be untyped or lack a conclusion."""

    id: str
    type: SchemeType | None = None
    scheme: str | None = None
    premises: tuple[str, ...] = ()
    conclusion: str | None = None


class Outline(_Model):
    """Graph in the shape of a patch, without the texts of resources."""

    resources: tuple[ResourceOutline, ...] = ()
    participants: tuple[ParticipantPatch, ...] = ()
    atoms: tuple[AtomPatch, ...] = ()
    schemes: tuple[SchemeOutline, ...] = ()
    major_claim: str | None = None
