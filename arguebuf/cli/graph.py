import shutil
import typing as t
from pathlib import Path

import typer

import arguebuf as ag
from arguebuf.cli.translator import Translator
from arguebuf.schema.graphviz import EdgeStyle
from arguebuf.schema.graphviz import export as to_gv

from . import model

cli = typer.Typer()


@cli.command()
def translate(
    input_folder: Path,
    source_lang: str,
    target_lang: str,
    auth_key: str,
    input_glob: str,
    output_folder: t.Optional[Path] = None,
    output_format: ag.GraphFormat = ag.GraphFormat.ARGUEBUF,
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
                graph = ag.Graph.from_file(path_pair.source)
                translator.translate(graph)
                graph.to_file(path_pair.target, output_format)


def _strip_node_labels(node: ag.Node) -> str:
    label: str = ""

    for char in node.label:
        if char.isspace():
            label += char
        else:
            label += "–"

    return label


@cli.command()
def render(
    input_folder: Path,
    input_glob: str,
    output_folder: t.Optional[Path] = None,
    output_format: str = ".pdf",
    strip_scheme_nodes: bool = False,
    strip_node_labels: bool = False,
    edge_style: t.Optional[EdgeStyle] = None,
    nodesep: t.Optional[float] = None,
    ranksep: t.Optional[float] = None,
    node_wrap_col: t.Optional[int] = None,
    node_margin: t.Tuple[float, float] = (0, 0),
    font_name: t.Optional[str] = None,
    font_size: t.Optional[float] = None,
    clean: bool = False,
    overwrite: bool = False,
    start: int = 1,
    max_nodes: t.Optional[int] = None,
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
                g = ag.Graph.from_file(path_pair.source)

                if strip_scheme_nodes:
                    g.strip_scheme_nodes()

                gv = to_gv(
                    g,
                    nodesep=nodesep,
                    ranksep=ranksep,
                    wrap_col=node_wrap_col,
                    margin=node_margin
                    if all(margin > 0 for margin in node_margin)
                    else None,
                    font_name=font_name,
                    font_size=font_size,
                    atom_label=_strip_node_labels if strip_node_labels else None,
                    scheme_label=_strip_node_labels if strip_node_labels else None,
                    edge_style=edge_style,
                    max_nodes=max_nodes,
                )
                ag.render(gv, path_pair.target)


@cli.command()
def convert(
    input_folder: Path,
    input_glob: str,
    output_folder: t.Optional[Path] = None,
    output_format: ag.GraphFormat = ag.GraphFormat.ARGUEBUF,
    clean: bool = False,
    overwrite: bool = False,
    start: int = 1,
    text_folder: t.Optional[Path] = None,
    text_glob: t.Optional[str] = None,
) -> None:
    if not output_folder:
        output_folder = input_folder

    texts: dict[str, str] = {}

    if text_folder and text_glob:
        for file in text_folder.glob(text_glob):
            with file.open("r") as f:
                filename = str(file.relative_to(text_folder).with_suffix(""))
                texts[filename] = f.read()

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
                graph = ag.Graph.from_file(path_pair.source)
                relative_source = str(
                    path_pair.source.relative_to(input_folder).with_suffix("")
                )

                if text := texts.get(relative_source):
                    graph.add_resource(ag.Resource(text))

                graph.to_file(path_pair.target, output_format)


@cli.command()
def statistics(
    input_folder: Path,
    input_glob: str,
):
    files = sorted(input_folder.glob(input_glob))

    graphs = [ag.Graph.from_file(file) for file in files]
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
