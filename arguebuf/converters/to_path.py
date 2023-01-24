from __future__ import annotations

import typing as t
from pathlib import Path

from arguebuf.converters.config import GraphFormat
from arguebuf.converters.to_io import to_io
from arguebuf.models.graph import Graph


def to_file(
    graph: Graph,
    path: t.Union[Path, str],
    format: GraphFormat = GraphFormat.ARGUEBUF,
    pretty: bool = False,
) -> None:
    """Export strucure of Graph instance into structure of File/Folder format."""
    if isinstance(path, str):
        path = Path(path)

    if path.is_dir() or not path.suffix:
        path = path / f"{graph.name}.json"

    with path.open("w", encoding="utf-8") as file:
        to_io(graph, file, format, pretty)


to_folder = to_file
