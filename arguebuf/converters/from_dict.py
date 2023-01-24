from __future__ import annotations

import typing as t

from arg_services.graph.v1 import graph_pb2
from google.protobuf.json_format import ParseDict

from arguebuf.converters.config import ConverterConfig, DefaultConverter
from arguebuf.converters.from_aif import from_aif
from arguebuf.converters.from_ova import from_ova
from arguebuf.converters.from_protobuf import from_protobuf
from arguebuf.models.graph import Graph
from arguebuf.schemas import aif, ova


def from_dict(
    obj: t.Mapping[str, t.Any],
    name: t.Optional[str] = None,
    config: ConverterConfig = DefaultConverter,
) -> Graph:
    """Generate Graph structure from DICT argument graph file(Link?)."""
    if "analysis" in obj:
        return from_ova(t.cast(ova.Graph, obj), name, config)

    if "locutions" in obj:
        return from_aif(t.cast(aif.Graph, obj), name, config)

    return from_protobuf(ParseDict(obj, graph_pb2.Graph()), name, config)
