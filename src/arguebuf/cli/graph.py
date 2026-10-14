from collections.abc import Callable
from pathlib import Path

import typer
from deepl import DeepLClient

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
    output_folder: Path | None = None,
    output_format: ag.dump.Format = ag.dump.Format.ARGUEBUF,
    clean: bool = False,
    overwrite: bool = False,
    start: int = 1,
) -> None:
    translator = Translator(DeepLClient(auth_key), source_lang, target_lang)

    for path_pair in model.pending_pairs(
        input_folder, output_folder, input_glob, ".json", clean, overwrite, start
    ):
        graph = ag.load.file(path_pair.source)
        translator.translate_graph(graph)
        ag.dump.file(graph, path_pair.target, ag.dump.Config(format=output_format))


def node_label_formatter(
    strip_labels: bool, strip_labels_char: str | None
) -> Callable[[ag.AbstractNode], str] | None:
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
    output_folder: Path | None = None,
    output_format: str = ".pdf",
    strip_scheme_nodes: bool = False,
    strip_node_labels: bool = False,
    strip_node_labels_char: str | None = None,
    edge_style: ag.schemas.graphviz.EdgeStyle = ag.schemas.graphviz.EdgeStyle.STEP,
    nodesep: float = 0.25,
    ranksep: float = 0.5,
    node_wrap_col: int = 36,
    node_margin: tuple[float, float] = (0.15, 0.1),
    font_name: str = "Arial",
    font_size: float = 11,
    clean: bool = False,
    overwrite: bool = False,
    start: int = 1,
    max_nodes: int = 1000,
    prog: str = "dot",
    dpi: int = 300,
    monochrome: bool = False,
) -> None:
    label_formatter = node_label_formatter(strip_node_labels, strip_node_labels_char)

    for path_pair in model.pending_pairs(
        input_folder, output_folder, input_glob, output_format, clean, overwrite, start
    ):
        g = ag.load.file(path_pair.source)

        if strip_scheme_nodes:
            g.strip_scheme_nodes()

        gv = ag.dump.graphviz(
            g,
            nodesep=nodesep,
            ranksep=ranksep,
            wrap_col=node_wrap_col,
            margin=node_margin,
            font_name=font_name,
            font_size=font_size,
            atom_label=label_formatter,
            scheme_label=label_formatter,
            edge_style=edge_style,
            max_nodes=max_nodes,
            monochrome=monochrome,
        )

        # graphs exceeding `max_nodes` are skipped
        if gv is not None:
            ag.render.graphviz(gv, path_pair.target, prog, dpi)


@cli.command()
def convert(
    input_folder: Path,
    input_glob: str,
    output_folder: Path | None = None,
    output_format: ag.dump.Format = ag.dump.Format.ARGUEBUF,
    clean: bool = False,
    overwrite: bool = False,
    start: int = 1,
    text_folder: Path | None = None,
    text_suffix: str = ".txt",
    reconstruct_dialog: bool = False,
) -> None:
    load_config = ag.load.Config(reconstruct_dialog=reconstruct_dialog)
    dump_config = ag.dump.Config(format=output_format)

    for path_pair in model.pending_pairs(
        input_folder, output_folder, input_glob, ".json", clean, overwrite, start
    ):
        text_file = (
            text_folder
            / path_pair.source.relative_to(input_folder).with_suffix(text_suffix)
            if text_folder
            else None
        )
        graph = ag.load.file(path_pair.source, text_file=text_file, config=load_config)
        ag.dump.file(graph, path_pair.target, dump_config)


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
