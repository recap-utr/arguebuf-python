import json
from typing import TextIO

from arguebuf.model import Graph

from ._config import Config, DefaultConfig
from ._dump_dict import dump_dict

__all__ = ("dump_json",)


def dump_json[T](graph: Graph[T], obj: TextIO, config: Config = DefaultConfig) -> None:
    """Export structure of Graph instance to JSON argument graph format."""
    json.dump(
        dump_dict(graph, config),
        obj,
        ensure_ascii=False,
        indent=2 if config.prettify else None,
    )
