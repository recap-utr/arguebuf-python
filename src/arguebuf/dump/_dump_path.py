from pathlib import Path, PurePath

from arguebuf.model import Graph
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject

from ._dump_json import dump_json
from ._format import Format

__all__ = ("dump_file",)


def dump_file[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
](
    graph: Graph[A, S, E, G, R, P, N],
    path: Path | str,
    *,
    format: Format = Format.ARGUEBUF,
    prettify: bool = True,
    codecs: Codecs[A, S, E, G, R, P, N] = DEFAULT_CODECS,
) -> None:
    """Export structure of Graph instance into a JSON file.

    If `path` is an existing folder, the file `<graph name>.json` is written into it,
    otherwise `path` is written as is.

    Raises:
        ValueError: If `path` is a folder and the graph has no name
            or its name is not a single path component (e.g., it contains a `/`).
    """
    path = Path(path)

    if path.is_dir():
        name = graph.name

        if not name or name == ".." or PurePath(name).name != name:
            raise ValueError(
                f"The graph name {name!r} cannot be used as a file name in '{path}'."
            )

        path = path / f"{name}.json"

    with path.open("w", encoding="utf-8") as file:
        dump_json(graph, file, format=format, prettify=prettify, codecs=codecs)
