import typing as t

import networkx as nx

from arguebuf.models.edge import Edge
from arguebuf.models.graph import Graph
from arguebuf.models.node import AbstractNode, AtomNode, SchemeNode


def to_networkx(
    graph: Graph,
    graph_attrs: t.Optional[t.MutableMapping[str, t.Callable[[Graph], t.Any]]] = None,
    atom_attrs: t.Optional[t.MutableMapping[str, t.Callable[[AtomNode], t.Any]]] = None,
    scheme_attrs: t.Optional[
        t.MutableMapping[str, t.Callable[[SchemeNode], t.Any]]
    ] = None,
    edge_attrs: t.Optional[t.MutableMapping[str, t.Callable[[Edge], t.Any]]] = None,
) -> nx.DiGraph:
    """Transform the argument graph for use with the library `NetworkX`

    This library allows you to apply advanced graph-related algorithms directly on your argument graphs.
    For instance, shortest paths and various distances can be computed.
    [Documentation](https://networkx.org/documentation/stable/reference/index.html)

    It is possible to add arbitrary attributes to the resulting graph and its elements.
    For this, you need to pass a dictionary with the desired name of the attribute and a function that is used to compute the attribute's value.
    The function will be passed the corresponding element as its only parameter.
    For instance, you could pass `atom_attrs={"text": lambda node: node.plain_text}` to set a `text` attribute for atom nodes.

    Args:
        graph_attrs: Attribute functions for the whole graph.
        atom_attrs: Attribute functions for the atom nodes.
        scheme_attrs: Attribute functions for the scheme nodes.
        edge_attrs: Attribute functions for the edges.

    Returns:
        Instance of the *directed* `NetworkX` graph.

    Examples:
        >>> g = Graph("Test")
        >>> n1 = AtomNode("Node1")
        >>> n2 = AtomNode("Node2")
        >>> e = Edge(n1, n2)
        >>> g.add_edge(e)
        >>> gnx = to_networkx(g)
        >>> gnx.number_of_nodes()
        2
    """

    if graph_attrs is None:
        graph_attrs = {}

    g = nx.DiGraph(None, **{key: func(graph) for key, func in graph_attrs.items()})

    for node in graph.atom_nodes.values():
        node_to_nx(node, g, atom_attrs)  # type: ignore

    for node in graph.scheme_nodes.values():
        node_to_nx(node, g, scheme_attrs)  # type: ignore

    for edge in graph.edges.values():
        edge_to_nx(edge, g, edge_attrs)

    return g


def edge_to_nx(
    edge: Edge,
    g: nx.DiGraph,
    attrs: t.Optional[t.MutableMapping[str, t.Callable[[Edge], t.Any]]] = None,
) -> None:
    """Submethod used to export Graph object g into NX Graph format."""

    if attrs is None:
        attrs = {}

    g.add_edge(
        edge.source.id,
        edge.target.id,
        **{key: func(edge) for key, func in attrs.items()},
    )


def node_to_nx(
    node: AbstractNode,
    g: nx.DiGraph,
    attrs: t.Optional[t.MutableMapping[str, t.Callable[[AbstractNode], t.Any]]] = None,
) -> None:
    """Submethod used to export Graph object g into NX Graph format."""
    if attrs is None:
        attrs = {}

    if "label" not in attrs:
        attrs["label"] = lambda x: x.label

    g.add_node(node._id, **{key: func(node) for key, func in attrs.items()})
