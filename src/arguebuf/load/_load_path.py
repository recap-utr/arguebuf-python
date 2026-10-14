from pathlib import Path

from arguebuf.model import Graph

from ._config import Config
from ._load_io import load_io

__all__ = ("load_file", "load_folder")


def load_file[T = str](
    file: Path | str,
    text_file: Path | str | None = None,
    config: Config[T] = Config(),
) -> Graph[T]:
    """Load a graph from a file.

    Args:
        file: Path of the graph, its suffix determines the format.
        text_file: Plain text added as a resource to the graph.
            Defaults to the path of `file` with the suffix `.txt`.
        config: Options for loading the graph.

    Returns:
        The loaded graph.
    """
    file = Path(file)
    text_file = Path(text_file) if text_file else file.with_suffix(".txt")

    with file.open(encoding="utf-8") as fp:
        graph = load_io(fp, file.suffix, file.stem, config)

    if text_file != file and text_file.exists():
        graph.add_resource(
            config.ResourceClass(config.parse(text_file.read_text(encoding="utf-8")))
        )

    return graph


def load_folder[T = str](
    folder: Path | str,
    pattern: str,
    text_folder: Path | str | None = None,
    text_suffix: str = ".txt",
    config: Config[T] = Config(),
) -> dict[Path, Graph[T]]:
    """Load all graphs matching the specified `pattern` in `folder`.

    Args:
        folder: Folder containing the graphs to be loaded.
        pattern: Unix glob pattern to filter the available files.
            Recursive matching can be achieved by prepending `**/` to any pattern.
            For instance, all `json` files of a folder can be retrieved with `**/*.json`.
            Supports the following wildcards: <https://docs.python.org/3/library/fnmatch.html#module-fnmatch>
        text_folder: Folder containing plain texts that are added as resources,
            mirroring the structure of `folder`.
        text_suffix: Suffix of the plain texts in `text_folder`.
        config: Options for loading the graphs.

    Returns:
        Dictionary containing all found file paths as well as the loaded graphs.
    """
    folder = Path(folder)
    text_folder = Path(text_folder) if text_folder else None

    return {
        file: load_file(
            file,
            text_folder / file.relative_to(folder).with_suffix(text_suffix)
            if text_folder
            else None,
            config,
        )
        for file in sorted(folder.glob(pattern))
    }
