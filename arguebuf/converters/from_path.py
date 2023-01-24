from __future__ import annotations

import typing as t
from pathlib import Path

from arguebuf.converters.config import ConverterConfig, DefaultConverter
from arguebuf.converters.from_io import from_io
from arguebuf.models.graph import Graph
from arguebuf.models.resource import Resource


def from_file(
    file: t.Union[Path, str],
    text_file: t.Optional[t.Union[Path, str]] = None,
    config: ConverterConfig = DefaultConverter,
) -> Graph:
    """Generate Graph structure from a File."""
    if isinstance(file, str):
        file = Path(file)

    with file.open("r", encoding="utf-8") as fp:
        graph = from_io(fp, file.suffix, file.stem, config)

    if not text_file:
        text_file = file.with_suffix(".txt")
    elif isinstance(text_file, str):
        text_file = Path(text_file)

    if text_file.exists():
        text = text_file.read_text()
        graph.add_resource(Resource(text))

    return graph


def from_folder(
    folder: t.Union[Path, str],
    pattern: str,
    text_folder: t.Optional[t.Union[Path, str]] = None,
    text_suffix: str = ".txt",
    config: ConverterConfig = DefaultConverter,
) -> t.Dict[Path, Graph]:
    """Load all graphs matching the specified `pattern` in `path`.

    Args:
        path: Folder containing the graphs to be loaded.
        pattern: Unix glob pattern to filter the available files.
            Recursive matching can be achieved by prepending `**/` to any pattern.
            For instance, all `json` files of a folder can be retrieved with `**/*.json`.
            Supports the following wildcards: <https://docs.python.org/3/library/fnmatch.html#module-fnmatch>
        atom_class: Allows to override the class used for atom nodes in case a specialized subclass has been created. Defaults to `AtomNode`.
        scheme_class: Allows to override the class used for scheme nodes in case a specialized subclass has been created. Defaults to `SchemeNode`.
        edge_class: Allows to override the class used for edges in case a specialized subclass has been created. Defaults to `Edge`.
        nlp: Optionally pass a function to transforms all texts of atom nodes and resources to arbitrary Python objects.
            Useful when using `spacy` to generate embeddings.
            In this case, you can load a model with `spacy.load(...)` and pass the resulting `nlp` function via this parameter.

    Returns:
        Dictionary containing all found file paths as well as the loaded graphs.
    """

    if isinstance(folder, str):
        folder = Path(folder)

    if isinstance(text_folder, str):
        text_folder = Path(text_folder)

    graphs: dict[Path, Graph] = {}

    for file in sorted(folder.glob(pattern)):
        text_file = None

        if text_folder:
            text_file = text_folder / file.relative_to(folder).with_suffix(text_suffix)

        graphs[file] = from_file(file, text_file, config)

    return graphs
