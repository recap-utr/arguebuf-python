"""Patches that change graphs by referencing their elements by id, e.g. written by agents."""

from arguebuf.patch._apply import PatchResult, apply_patch
from arguebuf.patch._outline import outline
from arguebuf.patch._schema import (
    AtomPatch,
    Outline,
    ParticipantPatch,
    Patch,
    ResourceOutline,
    ResourcePatch,
    SchemeOutline,
    SchemePatch,
)

__all__ = (
    "AtomPatch",
    "Outline",
    "ParticipantPatch",
    "Patch",
    "PatchResult",
    "ResourceOutline",
    "ResourcePatch",
    "SchemeOutline",
    "SchemePatch",
    "apply_patch",
    "outline",
)
