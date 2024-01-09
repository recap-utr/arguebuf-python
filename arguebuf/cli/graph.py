import shutil
import typing as t
from pathlib import Path

import typer

import arguebuf as ag

from . import model
from .translator import Translator

cli = typer.Typer()


@cli.command()
def translate(
    input_folder: Path,
    source_lang: str,
    target_lang: str,
    auth_key: str,
    input_glob: str,
    output_folder: t.Optional[Path] = None,
    output_format: ag.dump.Format = ag.dump.Format.ARGUEBUF,
    clean: bool = False,
    overwrite: bool = False,
    start: int = 1,
) -> None:
    if not output_folder:
        output_folder = input_folder

    if clean:
        shutil.rmtree(output_folder)
        output_folder.mkdir()

    path_pairs = model.PathPair.create(input_folder, output_folder, input_glob, ".json")
    translator = Translator(auth_key, source_lang, target_lang)
    bar: t.Iterable[model.PathPair]

    with typer.progressbar(
        path_pairs[start - 1 :],
        item_show_func=model.PathPair.label,
        show_pos=True,
    ) as bar:
        for path_pair in bar:
            if overwrite or not path_pair.target.exists():
                graph = ag.load.file(path_pair.source)
                translator.translate(graph)
                ag.dump.file(
                    graph, path_pair.target, ag.dump.Config(format=output_format)
                )


def node_label_formatter(
    strip_labels: bool, strip_labels_char: t.Optional[str]
) -> t.Callable[[ag.AbstractNode], str] | None:
    _replace_char = "–" if strip_labels_char is None else strip_labels_char

    def _node_label(node: ag.AbstractNode) -> str:
        return "".join(char if char.isspace() else _replace_char for char in node.label)

    if strip_labels:
        return _node_label

    return None


@cli.command()
def render(
    input_folder: Path,
    input_glob: str,
    output_folder: t.Optional[Path] = None,
    output_format: str = ".pdf",
    strip_scheme_nodes: bool = False,
    strip_node_labels: bool = False,
    strip_node_labels_char: t.Optional[str] = None,
    edge_style: t.Optional[ag.schemas.graphviz.EdgeStyle] = None,
    nodesep: t.Optional[float] = None,
    ranksep: t.Optional[float] = None,
    node_wrap_col: t.Optional[int] = None,
    node_margin: tuple[float, float] = (0, 0),
    font_name: t.Optional[str] = None,
    font_size: t.Optional[float] = None,
    clean: bool = False,
    overwrite: bool = False,
    start: int = 1,
    max_nodes: t.Optional[int] = None,
    prog: str = "dot",
    dpi: int = 300,
    monochrome: bool = False,
) -> None:
    if not output_folder:
        output_folder = input_folder

    if clean:
        shutil.rmtree(output_folder)
        output_folder.mkdir()

    paths = model.PathPair.create(
        input_folder, output_folder, input_glob, output_format
    )
    bar: t.Iterable[model.PathPair]

    with typer.progressbar(
        paths[start - 1 :],
        item_show_func=model.PathPair.label,
        show_pos=True,
    ) as bar:
        for path_pair in bar:
            if overwrite or not path_pair.target.exists():
                g = ag.load.file(path_pair.source)

                if strip_scheme_nodes:
                    g.strip_scheme_nodes()

                gv = ag.dump.graphviz(
                    g,
                    nodesep=nodesep,
                    ranksep=ranksep,
                    wrap_col=node_wrap_col,
                    margin=(
                        node_margin
                        if all(margin > 0 for margin in node_margin)
                        else None
                    ),
                    font_name=font_name,
                    font_size=font_size,
                    atom_label=node_label_formatter(
                        strip_node_labels, strip_node_labels_char
                    ),
                    scheme_label=node_label_formatter(
                        strip_node_labels, strip_node_labels_char
                    ),
                    edge_style=edge_style,
                    max_nodes=max_nodes,
                    monochrome=monochrome,
                )
                ag.render.graphviz(gv, path_pair.target, prog, dpi)


@cli.command()
def convert(
    input_folder: Path,
    input_glob: str,
    output_folder: t.Optional[Path] = None,
    output_format: ag.dump.Format = ag.dump.Format.ARGUEBUF,
    clean: bool = False,
    overwrite: bool = False,
    start: int = 1,
    text_folder: t.Optional[Path] = None,
    text_suffix: str = ".txt",
) -> None:
    if not output_folder:
        output_folder = input_folder

    if clean:
        shutil.rmtree(output_folder)
        output_folder.mkdir()

    paths = model.PathPair.create(input_folder, output_folder, input_glob, ".json")
    bar: t.Iterable[model.PathPair]

    with typer.progressbar(
        paths[start - 1 :],
        item_show_func=model.PathPair.label,
        show_pos=True,
    ) as bar:
        for path_pair in bar:
            if overwrite or not path_pair.target.exists():
                text_file = None

                if text_folder:
                    text_file = text_folder / path_pair.source.relative_to(
                        input_folder
                    ).with_suffix(text_suffix)

                graph = ag.load.file(path_pair.source, text_file=text_file)

                ag.dump.file(
                    graph, path_pair.target, ag.dump.Config(format=output_format)
                )


@cli.command()
def statistics(
    input_folder: Path,
    input_glob: str,
):
    files = sorted(input_folder.glob(input_glob))

    graphs = [ag.load.file(file) for file in files]
    atom_nodes = [len(graph.atom_nodes) for graph in graphs]
    scheme_nodes = [len(graph.scheme_nodes) for graph in graphs]
    edges = [len(graph.edges) for graph in graphs]

    total_graphs = len(graphs)
    total_atom_nodes = sum(atom_nodes)
    total_scheme_nodes = sum(scheme_nodes)
    total_edges = sum(edges)

    typer.echo(
        f"""Total Graphs: {total_graphs}

Total Atom Nodes: {total_atom_nodes}
Total Scheme Nodes: {total_scheme_nodes}
Total Edges: {total_edges}

Atom Nodes per Graph: {total_atom_nodes / total_graphs}
Scheme Nodes per Graph: {total_scheme_nodes / total_graphs}
Edges per Graph: {total_edges / total_graphs}

Max. Atom Nodes: {max(atom_nodes)}
Max. Scheme Nodes: {max(scheme_nodes)}
Max. Edges: {max(edges)}

Min. Atom Nodes: {min(atom_nodes)}
Min. Scheme Nodes: {min(scheme_nodes)}
Min. Edges: {min(edges)}"""
    )
