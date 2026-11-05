from typing import Literal, TypeAlias

__all__ = ("Format",)

# a classic alias, since typer cannot read `type` aliases
Format: TypeAlias = Literal["arguebuf", "aif", "xaif"]  # noqa: UP040
"""Formats supported by `arguebuf.dump.dict`."""
