import copy
from dataclasses import dataclass
from typing import TypeIs, cast

from jsonschema import Draft7Validator

from arguebuf.model.issue import Issue, issue
from arguebuf.model.userdata import JsonValue
from arguebuf.patch._schema import PATCH_SCHEMA, JsonSchema, Patch

__all__ = ("ParsedPatch", "parse_patch")


@dataclass(slots=True, frozen=True)
class ParsedPatch:
    """Validated patch or all validation failures with their paths."""

    patch: Patch | None = None
    issues: tuple[Issue, ...] = ()


def _is_patch(value: object, schema: JsonSchema, issues: list[Issue]) -> TypeIs[Patch]:
    for error in Draft7Validator(schema).iter_errors(cast(JsonValue, value)):
        issues.append(
            copy.replace(
                issue("invalid-patch", error.message), path=tuple(error.absolute_path)
            )
        )

    return not issues


def parse_patch(value: object, *, schema: JsonSchema = PATCH_SCHEMA) -> ParsedPatch:
    """Validate untrusted input against `PATCH_SCHEMA` or a host extension.

    All failures are reported as `invalid-patch` issues using JSON Schema paths.
    Valid host fields are kept in the returned patch.

    Examples:
        >>> parse_patch({"atoms": [{"id": "a", "text": "Claim"}]}).issues
        ()
    """
    issues: list[Issue] = []

    return ParsedPatch(value if _is_patch(value, schema, issues) else None, tuple(issues))
