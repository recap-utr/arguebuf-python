from pathlib import Path

from pygraphviz import AGraph

__all__ = ("graphviz",)


def graphviz(
    graph: AGraph,
    path: Path | str,
    prog: str = "dot",
    dpi: int = 300,
) -> None:
    """Render a graph created by `arguebuf.dump.graphviz`.

    The output format is derived from the suffix of `path`.
    """
    graph.graph_attr["dpi"] = str(dpi)
    graph.draw(path=str(path), prog=prog)
