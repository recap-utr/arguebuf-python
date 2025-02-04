import typing as t

from arguebuf.model import Graph

from ._config import Config, DefaultConfig
from ._dump_json import dump_json

__all__ = ("dump_io",)


def dump_io(graph: Graph, obj: t.TextIO, config: Config = DefaultConfig) -> None:
    """Export structure of Graph instance to IO argument graph format."""
    dump_json(graph, obj, config)
