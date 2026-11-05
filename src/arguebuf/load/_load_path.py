from pathlib import Path

from arguebuf.model import Graph
from arguebuf.model.issue import Reporter
from arguebuf.model.resource import Resource
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject

from ._load_io import load_io

__all__ = ("load_file", "load_folder")


def load_file[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    file: Path | str,
    text_file: Path | str | None = None,
    *,
    reconstruct_dialog: bool = False,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, R, P, N, G]:
    """Load a graph from a file.

    Args:
        file: Path of the graph, its suffix determines the format.
        text_file: Plain text added as a resource to the graph.
            Defaults to the path of `file` with the suffix `.txt`.
        reconstruct_dialog: Reconstruct the dialog of AIF and xAIF graphs
            (see `load_aif`), ignored for other formats.
        codecs: Codecs loading the userdata.

    Returns:
        The loaded graph.
    """
    file = Path(file)
    text_file = Path(text_file) if text_file else file.with_suffix(".txt")

    with file.open(encoding="utf-8") as fp:
        graph = load_io(
            fp,
            file.suffix,
            file.stem,
            reconstruct_dialog=reconstruct_dialog,
            codecs=codecs, on_issue=on_issue, strict=strict,
        )

    if text_file != file and text_file.exists():
        # some corpora (e.g. us-2016) contain texts that are not valid UTF-8
        text = text_file.read_text(encoding="utf-8", errors="replace")
        graph = graph.edit(
            lambda draft: draft.add_resource(
                Resource(text, userdata=codecs.resource.validate_python({}))
            )
        )

    return graph


def load_folder[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    folder: Path | str,
    pattern: str,
    text_folder: Path | str | None = None,
    text_suffix: str = ".txt",
    *,
    reconstruct_dialog: bool = False,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> dict[Path, Graph[A, S, E, R, P, N, G]]:
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
        reconstruct_dialog: Reconstruct the dialog of AIF and xAIF graphs
            (see `load_aif`), ignored for other formats.
        codecs: Codecs loading the userdata.

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
            reconstruct_dialog=reconstruct_dialog,
            codecs=codecs, on_issue=on_issue, strict=strict,
        )
        for file in sorted(folder.glob(pattern))
    }
