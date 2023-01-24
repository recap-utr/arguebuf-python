from __future__ import annotations

import typing as t

from arguebuf.converters.config import ConverterConfig, DefaultConverter
from arguebuf.converters.from_aml import from_aml
from arguebuf.converters.from_brat import from_brat
from arguebuf.converters.from_json import from_json
from arguebuf.converters.from_kialo import from_kialo
from arguebuf.converters.from_microtexts import from_microtexts
from arguebuf.models.graph import Graph


def from_io(
    obj: t.TextIO,
    suffix: str,
    name: t.Optional[str] = None,
    config: ConverterConfig = DefaultConverter,
) -> Graph:
    """Generate Graph structure from IO argument graph file(Link?)."""

    if suffix == ".ann":
        return from_brat(obj, name, config)
    if suffix == ".txt":
        return from_kialo(obj, name, config)
    if suffix == ".aml":
        return from_aml(obj, name, config)
    if suffix == ".xml":
        return from_microtexts(obj, name, config)

    return from_json(obj, name, config)
