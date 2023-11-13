import json
import typing as t

from arguebuf.model import Graph

from ._config import Config, DefaultConfig
from ._load_dict import load_dict

__all__ = ("load_json",)


def load_json(
    obj: t.TextIO,
    name: t.Optional[str] = None,
    config: Config = DefaultConfig,
) -> Graph:
    """Generate Graph structure from JSON argument graph file(Link?)."""
    return load_dict(json.load(obj), name, config)
