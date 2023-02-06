from __future__ import annotations

import typing as t

from arguebuf.model import Graph

from .config import Config, DefaultConfig
from .load_aml import load_aml
from .load_brat import load_brat
from .load_json import load_json
from .load_kialo import load_kialo
from .load_microtexts import load_microtexts

__all__ = ("load_io",)


def load_io(
    obj: t.TextIO,
    suffix: str,
    name: t.Optional[str] = None,
    config: Config = DefaultConfig,
) -> Graph:
    """Generate Graph structure from IO argument graph file(Link?)."""

    if suffix == ".ann":
        return load_brat(obj, name, config)
    if suffix == ".txt":
        return load_kialo(obj, name, config)
    if suffix == ".aml":
        return load_aml(obj, name, config)
    if suffix == ".xml":
        return load_microtexts(obj, name, config)

    return load_json(obj, name, config)
