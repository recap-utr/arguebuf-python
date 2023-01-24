from __future__ import annotations

import json
import typing as t

from arguebuf.converters.config import ConverterConfig, DefaultConverter
from arguebuf.converters.from_dict import from_dict
from arguebuf.models.graph import Graph


def from_json(
    obj: t.TextIO,
    name: t.Optional[str] = None,
    config: ConverterConfig = DefaultConverter,
) -> Graph:
    """Generate Graph structure from JSON argument graph file(Link?)."""
    return from_dict(json.load(obj), name, config)
