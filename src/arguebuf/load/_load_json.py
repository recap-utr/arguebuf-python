import json
from typing import TextIO

from arguebuf.model import Graph

from ._config import Config
from ._load_dict import load_dict

__all__ = ("load_json",)


def load_json[T = str](
    obj: TextIO,
    name: str | None = None,
    config: Config[T] = Config(),
) -> Graph[T]:
    """Generate Graph structure from JSON argument graph file."""
    return load_dict(json.load(obj), name, config)
