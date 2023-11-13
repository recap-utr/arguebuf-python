import typing as t
from pathlib import Path

from arguebuf.model import Graph

from ._config import Config, DefaultConfig
from ._dump_io import dump_io

__all__ = ("dump_file",)


def dump_file(
    graph: Graph, path: t.Union[Path, str], config: Config = DefaultConfig
) -> None:
    """Export strucure of Graph instance into structure of File/Folder format."""
    if isinstance(path, str):
        path = Path(path)

    if path.is_dir():
        path = path / f"{graph.name}.json"
    elif not path.suffix:
        path = path.with_suffix(".json")

    with path.open("w", encoding="utf-8") as file:
        dump_io(graph, file, config)
