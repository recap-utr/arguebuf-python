"""Patches that change graphs by referencing their elements by id, e.g. written by agents."""

from arguebuf.patch._apply import PatchResult, apply_patch
from arguebuf.patch._outline import outline
from arguebuf.patch._parse import ParsedPatch, parse_patch
from arguebuf.patch._schema import (
    PATCH_SCHEMA,
    AtomPatch,
    Outline,
    ParticipantPatch,
    Patch,
    ResourcePatch,
    SchemePatch,
)
from arguebuf.patch._schema import (
    JsonSchema as JsonSchema,
)

__all__ = (
    "PATCH_SCHEMA",
    "AtomPatch",
    "Outline",
    "ParsedPatch",
    "ParticipantPatch",
    "Patch",
    "PatchResult",
    "ResourcePatch",
    "SchemePatch",
    "apply_patch",
    "outline",
    "parse_patch",
)
