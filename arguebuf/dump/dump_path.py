from __future__ import annotations

import typing as t
from pathlib import Path

from arguebuf.model import Graph

from .config import Config, DefaultConfig
from .dump_io import dump_io

__all__ = ("dump_file",)


def dump_file(
    graph: Graph, path: t.Union[Path, str], config: Config = DefaultConfig
) -> None:
    """Export strucure of Graph instance into structure of File/Folder format."""
    if isinstance(path, str):
        path = Path(path)

    if path.is_dir() or not path.suffix:
        path = path / f"{graph.name}.json"

    with path.open("w", encoding="utf-8") as file:
        dump_io(graph, file, config)
