from collections.abc import Callable, Mapping
from typing import Any

import networkx as nx

from arguebuf.model import Graph
from arguebuf.model.edge import Edge
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode

__all__ = ("dump_networkx",)

# lazily evaluated since networkx graphs are only generic in their type stubs
type DiGraph = nx.DiGraph[str]


def dump_networkx[T](
    graph: Graph[T],
    graph_attrs: Mapping[str, Callable[[Graph[T]], Any]] | None = None,
    atom_attrs: Mapping[str, Callable[[AtomNode[T]], Any]] | None = None,
    scheme_attrs: Mapping[str, Callable[[SchemeNode], Any]] | None = None,
    edge_attrs: Mapping[str, Callable[[Edge], Any]] | None = None,
) -> DiGraph:
    """Transform the argument graph for use with the library `NetworkX`

    This library allows you to apply advanced graph-related algorithms directly on your argument graphs.
    For instance, shortest paths and various distances can be computed.
    [Documentation](https://networkx.org/documentation/stable/reference/index.html)

    It is possible to add arbitrary attributes to the resulting graph and its elements.
    For this, you need to pass a dictionary with the desired name of the attribute and a function that is used to compute the attribute's value.
    The function will be passed the corresponding element as its only parameter.
    For instance, you could pass `atom_attrs={"text": lambda node: node.plain_text}` to set a `text` attribute for atom nodes.
    All nodes have a `label` attribute unless it is overridden.

    Args:
        graph: The graph to transform.
        graph_attrs: Attribute functions for the whole graph.
        atom_attrs: Attribute functions for the atom nodes.
        scheme_attrs: Attribute functions for the scheme nodes.
        edge_attrs: Attribute functions for the edges.

    Returns:
        Instance of the *directed* `NetworkX` graph.

    Examples:
        >>> from arguebuf import AtomNode, Edge, Graph
        >>> g = Graph("Test")
        >>> g.add_edge(Edge(AtomNode("Node1"), AtomNode("Node2")))
        >>> gnx = dump_networkx(g)
        >>> gnx.number_of_nodes()
        2
    """
    g: DiGraph = nx.DiGraph(None, **_attrs(graph, graph_attrs))

    for atom in graph.atom_nodes.values():
        g.add_node(atom.id, **_node_attrs(atom, atom_attrs))

    for scheme in graph.scheme_nodes.values():
        g.add_node(scheme.id, **_node_attrs(scheme, scheme_attrs))

    for edge in graph.edges.values():
        g.add_edge(edge.source.id, edge.target.id, **_attrs(edge, edge_attrs))

    return g


def _attrs[E](
    element: E, attrs: Mapping[str, Callable[[E], Any]] | None
) -> dict[str, Any]:
    return {key: func(element) for key, func in (attrs or {}).items()}


def _node_attrs[N: AbstractNode](
    node: N, attrs: Mapping[str, Callable[[N], Any]] | None
) -> dict[str, Any]:
    return {"label": node.label, **_attrs(node, attrs)}
