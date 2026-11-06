"""Field types shared by the schemas of the JSON formats."""

from typing import Annotated

from pydantic import Field

__all__ = ("Id",)

type Id = Annotated[str, Field(coerce_numbers_to_str=True)]
"""Id of a JSON format, numbers are converted to strings."""
