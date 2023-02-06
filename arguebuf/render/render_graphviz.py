import typing as t
from pathlib import Path

from graphviz import ENGINES, FORMATS, Digraph

from arguebuf.model import Graph
from arguebuf.schemas.graphviz import GraphvizGraph

__all__ = ("graphviz",)


def graphviz(
    graph: GraphvizGraph,
    path: t.Union[Path, str],
    prog: str = "dot",
) -> None:
    """Visualize a Graph instance using a GraphViz backend. Make sure that a GraphViz Executable path is set on your machine for visualization."""
    if isinstance(path, str):
        path = Path(path)

    if path.suffix.removeprefix(".") not in FORMATS:
        raise ValueError(
            f"You need to provide a path with a file ending supported by graphviz: {FORMATS}"
        )

    if prog not in ENGINES:
        raise ValueError(
            f"You need to provide a prog that is supported by graphviz: {ENGINES}"
        )

    if isinstance(graph, Graph):
        raise ValueError(
            "This method expects a graph in the 'DOT' format."
            "Please use 'arguebuf.to_graphviz(graph)' to convert your argument graph to the 'DOT' format."
        )
    elif isinstance(graph, Digraph):
        graph.render(outfile=path, engine=prog)
    else:
        graph.draw(path=path, prog=prog)
