from __future__ import annotations

import typing as t

from google.protobuf.json_format import MessageToDict

from arguebuf.converters.config import GraphFormat
from arguebuf.converters.to_aif import to_aif
from arguebuf.converters.to_protobuf import to_protobuf
from arguebuf.models.graph import Graph


def to_dict(graph: Graph, format: GraphFormat) -> t.Dict[str, t.Any]:
    """Export structure of Graph instance to DICT argument graph format."""

    if format == GraphFormat.AIF:
        return t.cast(dict[str, t.Any], to_aif(graph))

    return MessageToDict(to_protobuf(graph), including_default_value_fields=False)
