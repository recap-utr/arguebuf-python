from collections.abc import Callable, Mapping

import networkx as nx

from arguebuf.model import Graph
from arguebuf.model.edge import Edge
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode

__all__ = ("dump_networkx",)

# lazily evaluated since networkx graphs are only generic in their type stubs
type DiGraph = nx.DiGraph[str]


def dump_networkx[A, S, E, G, R, P, N](
    graph: Graph[A, S, E, G, R, P, N],
    graph_attrs: Mapping[str, Callable[[Graph[A, S, E, G, R, P, N]], object]]
    | None = None,
    atom_attrs: Mapping[str, Callable[[AtomNode[A]], object]] | None = None,
    scheme_attrs: Mapping[str, Callable[[SchemeNode[S]], object]] | None = None,
    edge_attrs: Mapping[str, Callable[[Edge[E]], object]] | None = None,
) -> DiGraph:
    """Transform the argument graph for use with the library `NetworkX`

    This library allows you to apply advanced graph-related algorithms directly on your argument graphs.
    For instance, shortest paths and various distances can be computed.
    [Documentation](https://networkx.org/documentation/stable/reference/index.html)

    It is possible to add arbitrary attributes to the resulting graph and its elements.
    For this, you need to pass a dictionary with the desired name of the attribute and a function that is used to compute the attribute's value.
    The function will be passed the corresponding element as its only parameter.
    For instance, you could pass `atom_attrs={"text": lambda node: node.text}` to set a `text` attribute for atom nodes.
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
        >>> n1, n2 = AtomNode("Node1"), AtomNode("Node2")
        >>> g.add_node(n1)
        >>> g.add_node(n2)
        >>> g.add_edge(Edge(n1, n2))
        >>> gnx = dump_networkx(g)
        >>> gnx.number_of_nodes()
        2
    """
    g: DiGraph = nx.DiGraph()
    g.graph.update(_attrs(graph, graph_attrs))

    for atom in graph.atom_nodes.values():
        g.add_node(atom.id)
        g.nodes[atom.id].update(_node_attrs(atom, atom_attrs))

    for scheme in graph.scheme_nodes.values():
        g.add_node(scheme.id)
        g.nodes[scheme.id].update(_node_attrs(scheme, scheme_attrs))

    for edge in graph.edges.values():
        g.add_edge(edge.source.id, edge.target.id)
        g.edges[edge.source.id, edge.target.id].update(_attrs(edge, edge_attrs))

    return g


def _attrs[T](
    element: T, attrs: Mapping[str, Callable[[T], object]] | None
) -> dict[str, object]:
    return {key: func(element) for key, func in (attrs or {}).items()}


def _node_attrs[T: AbstractNode](
    node: T, attrs: Mapping[str, Callable[[T], object]] | None
) -> dict[str, object]:
    return {"label": node.label, **_attrs(node, attrs)}
