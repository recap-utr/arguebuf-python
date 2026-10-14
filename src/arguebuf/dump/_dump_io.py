from typing import TextIO

from arguebuf.model import Graph

from ._config import Config, DefaultConfig
from ._dump_json import dump_json

__all__ = ("dump_io",)


def dump_io[T](graph: Graph[T], obj: TextIO, config: Config = DefaultConfig) -> None:
    """Export structure of Graph instance to a file object."""
    dump_json(graph, obj, config)
