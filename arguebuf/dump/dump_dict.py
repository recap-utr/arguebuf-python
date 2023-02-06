from __future__ import annotations

import typing as t

from google.protobuf.json_format import MessageToDict

from arguebuf.model import Graph

from .config import Config, DefaultConfig, Format
from .dump_aif import dump_aif
from .dump_protobuf import dump_protobuf

__all__ = ("dump_dict",)


def dump_dict(graph: Graph, config: Config = DefaultConfig) -> t.Dict[str, t.Any]:
    """Export structure of Graph instance to DICT argument graph format."""

    if config.format == Format.AIF:
        return t.cast(dict[str, t.Any], dump_aif(graph))

    return MessageToDict(dump_protobuf(graph), including_default_value_fields=False)
