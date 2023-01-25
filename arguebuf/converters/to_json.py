from __future__ import annotations

import json
import typing as t

from arguebuf.converters.config import GraphFormat
from arguebuf.converters.to_dict import to_dict
from arguebuf.models.graph import Graph


def to_json(
    graph: Graph,
    obj: t.TextIO,
    format: GraphFormat = GraphFormat.ARGUEBUF,
    pretty: bool = False,
) -> None:
    """Export structure of Graph instance to JSON argument graph format."""
    json.dump(
        to_dict(graph, format),
        obj,
        ensure_ascii=False,
        indent=4 if pretty else None,
    )