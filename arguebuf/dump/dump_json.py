from __future__ import annotations

import typing as t
from json import dump as pyjson_dump

from arguebuf.model import Graph

from .config import Config, DefaultConfig
from .dump_dict import dump_dict

__all__ = ("dump_json",)


def dump_json(graph: Graph, obj: t.TextIO, config: Config = DefaultConfig) -> None:
    """Export structure of Graph instance to JSON argument graph format."""
    pyjson_dump(
        dump_dict(graph, config),
        obj,
        ensure_ascii=False,
        indent=2 if config.prettify else None,
    )
