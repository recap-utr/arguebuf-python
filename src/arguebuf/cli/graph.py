from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer
from deepl import DeepLClient

import arguebuf as ag

from . import model
from .translator import Translator

cli = typer.Typer(no_args_is_help=True)

OutputFormat = Annotated[
    ag.dump.Format, typer.Option(help="Format of the exported graphs.")
]


@cli.command()
def translate(
    input_folder: model.InputFolder,
    source_lang: model.SourceLang,
    target_lang: model.TargetLang,
    auth_key: model.AuthKey,
    input_glob: model.InputGlob,
    output_folder: model.OutputFolder = None,
    output_format: OutputFormat = ag.dump.Format.ARGUEBUF,
    clean: model.Clean = False,
    overwrite: model.Overwrite = False,
    start: model.Start = 1,
) -> None:
    """Translate the texts of atom nodes, references, and resources with DeepL."""
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
    input_folder: model.InputFolder,
    input_glob: model.InputGlob,
    output_folder: model.OutputFolder = None,
    output_format: Annotated[
        str,
        typer.Option(
            help="Suffix of the rendered files that determines their format,"
            " e.g., '.pdf', '.png', or '.svg'."
        ),
    ] = ".pdf",
    strip_scheme_nodes: Annotated[
        bool,
        typer.Option(help="Remove scheme nodes and connect their atoms directly."),
    ] = False,
    strip_node_labels: Annotated[
        bool,
        typer.Option(help="Mask node labels, e.g., to show only the structure."),
    ] = False,
    strip_node_labels_char: Annotated[
        str | None,
        typer.Option(
            help="Character replacing all non-whitespace characters of masked labels,"
            " defaults to an en dash.",
            show_default=False,
        ),
    ] = None,
    edge_style: Annotated[
        ag.schemas.graphviz.EdgeStyle, typer.Option(help="Shape of the edges.")
    ] = ag.schemas.graphviz.EdgeStyle.STEP,
    nodesep: Annotated[
        float,
        typer.Option(help="Minimum space between nodes of the same rank in inches."),
    ] = 0.25,
    ranksep: Annotated[
        float, typer.Option(help="Minimum space between ranks in inches.")
    ] = 0.5,
    node_wrap_col: Annotated[
        int, typer.Option(help="Maximum number of characters per line in labels.")
    ] = 36,
    node_margin: Annotated[
        tuple[float, float],
        typer.Option(help="Horizontal and vertical padding of labels in inches."),
    ] = (0.15, 0.1),
    font_name: Annotated[str, typer.Option(help="Font of the labels.")] = "Arial",
    font_size: Annotated[
        float, typer.Option(help="Font size of the labels in points.")
    ] = 11,
    clean: model.Clean = False,
    overwrite: model.Overwrite = False,
    start: model.Start = 1,
    max_nodes: Annotated[
        int, typer.Option(help="Skip graphs with more nodes than this limit.")
    ] = 1000,
    prog: Annotated[
        str, typer.Option(help="Graphviz layout engine, e.g., 'dot' or 'neato'.")
    ] = "dot",
    dpi: Annotated[
        int, typer.Option(help="Resolution of raster formats such as PNG.")
    ] = 300,
    monochrome: Annotated[
        bool, typer.Option(help="Render in black and white instead of color.")
    ] = False,
) -> None:
    """Render graphs as images with Graphviz."""
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
    input_folder: model.InputFolder,
    input_glob: model.InputGlob,
    output_folder: model.OutputFolder = None,
    output_format: OutputFormat = ag.dump.Format.ARGUEBUF,
    clean: model.Clean = False,
    overwrite: model.Overwrite = False,
    start: model.Start = 1,
    text_folder: Annotated[
        Path | None,
        typer.Option(
            help="Folder mirroring INPUT_FOLDER with plain texts to add as resources,"
            " defaults to the text files next to the graphs.",
            show_default=False,
        ),
    ] = None,
    text_suffix: Annotated[
        str, typer.Option(help="Suffix of the files in TEXT_FOLDER.")
    ] = ".txt",
    reconstruct_dialog: Annotated[
        bool,
        typer.Option(
            help="Connect AIF and xAIF atoms only linked through dialog nodes"
            " to the atoms of adjacent turns, otherwise they become isolated."
        ),
    ] = False,
) -> None:
    """Convert graphs between formats, the input format is derived from the suffix."""
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
    input_folder: Annotated[
        Path,
        typer.Argument(
            help="Folder to search with INPUT_GLOB.", exists=True, file_okay=False
        ),
    ],
    input_glob: model.InputGlob,
) -> None:
    """Print node and edge counts of the selected graphs."""
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
