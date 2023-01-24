from __future__ import annotations

import typing as t

from arguebuf.converters.config import GraphFormat
from arguebuf.converters.to_json import to_json
from arguebuf.models.graph import Graph


def to_io(
    graph: Graph,
    obj: t.TextIO,
    format: GraphFormat = GraphFormat.ARGUEBUF,
    pretty: bool = False,
) -> None:
    """Export structure of Graph instance to IO argument graph format."""
    to_json(graph, obj, format, pretty)
