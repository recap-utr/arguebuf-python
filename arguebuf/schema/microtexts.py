import typing as t
from dataclasses import dataclass
from enum import Enum

from lxml import etree

import arguebuf as ag
from arguebuf import AtomNode, Edge, Graph, SchemeNode
from arguebuf.services import utils


class EdgeType(Enum):
    SEGMENTATION = "seg"
    SUPPORT_DEFAULT = "sup"
    SUPPORT_EXAMPLE = "exa"
    ADDITIONAL_SOURCE = "add"
    ATTACK_ATOM = "reb"
    ATTACK_SCHEME = "und"


@dataclass
class _Edge:
    source: str
    target: str
    type: EdgeType


def transform_edges(elems: t.Iterable[t.Any]) -> dict[str, _Edge]:
    return {
        str(elem.attrib["id"]): _Edge(
            str(elem.attrib["src"]),
            str(elem.attrib["trg"]),
            EdgeType(str(elem.attrib["type"])),
        )
        for elem in elems
        if isinstance(elem, etree._Element)
    }


def from_microtexts(
    obj: t.IO,
    name: t.Optional[str] = None,
    graph_class: t.Type[Graph] = Graph,
    atom_class: t.Type[AtomNode] = AtomNode,
    scheme_class: t.Type[SchemeNode] = SchemeNode,
    edge_class: t.Type[Edge] = Edge,
    nlp: t.Optional[t.Callable[[str], t.Any]] = None,
) -> Graph:
    """
    Generate Graph structure from AML argument graph file
    ElementTree XML API: https://docs.python.org/3/library/xml.etree.elementtree.html#
    """

    tree = etree.parse(obj)
    root = tree.getroot()
    id = root.get("id")
    g = graph_class(name or id)
    g.userdata = {"stance": root.get("stance"), "topic": root.get("topic_id")}

    segmentation_edge_tags = root.xpath("//edge[@type='seg']")
    atom_edge_tags = root.xpath("//edge[@type='sup' or @type='exa' or @type='reb']")
    scheme_edge_tags = root.xpath("//edge[@type='add']")
    edge_edge_tags = root.xpath("//edge[@type='und']")
    edu_tags = root.xpath("//edu")
    joint_tags = root.xpath("//joint")
    adu_tags = root.xpath("//adu")
    assert (
        isinstance(edu_tags, list)
        and isinstance(joint_tags, list)
        and isinstance(adu_tags, list)
        and isinstance(segmentation_edge_tags, list)
        and isinstance(atom_edge_tags, list)
        and isinstance(edge_edge_tags, list)
        and isinstance(scheme_edge_tags, list)
    )

    source_tags = {
        str(elem.attrib["id"]): elem
        for elem in [*edu_tags, *joint_tags]
        if isinstance(elem, etree._Element)
    }
    adu2source = {
        edge.target: edge.source
        for edge in transform_edges(segmentation_edge_tags).values()
    }
    atom_edges = transform_edges(atom_edge_tags)
    scheme_edges = transform_edges(scheme_edge_tags)
    edge_edges = transform_edges(edge_edge_tags)

    for adu in adu_tags:
        if isinstance(adu, etree._Element) and (adu_id := adu.get("id")):
            adu_source_id = adu2source[adu_id]
            adu_source = source_tags[adu_source_id]

            if adu_source.text is not None:
                atom = atom_class(utils.parse(adu_source.text, nlp), id=adu_id)

                if type := adu.get("type"):
                    atom.userdata["type"] = type

                g.add_node(atom)

    for edge_id, edge in atom_edges.items():
        scheme_node = scheme_class(id=edge_id)

        if edge.type == EdgeType.SUPPORT_DEFAULT:
            scheme_node.scheme = ag.Support.DEFAULT
        elif edge.type == EdgeType.SUPPORT_EXAMPLE:
            scheme_node.scheme = ag.Support.EXAMPLE
        elif edge.type == EdgeType.ATTACK_ATOM:
            scheme_node.scheme = ag.Attack.DEFAULT

        if (source_atom := g.atom_nodes.get(edge.source)) and (
            target_atom := g.atom_nodes.get(edge.target)
        ):
            g.add_edge(edge_class(source_atom, scheme_node))
            g.add_edge(edge_class(scheme_node, target_atom))

    for edge in scheme_edges.values():
        if (scheme_node := g.scheme_nodes.get(edge.target)) and (
            atom_node := g.atom_nodes.get(edge.source)
        ):
            g.add_edge(edge_class(atom_node, scheme_node))

    for edge_id, edge in edge_edges.items():
        if (target_scheme := g.scheme_nodes.get(edge.target)) and (
            atom_node := g.atom_nodes.get(edge.source)
        ):
            source_scheme = scheme_class(id=edge_id)
            g.add_edge(edge_class(atom_node, source_scheme))
            g.add_edge(edge_class(source_scheme, target_scheme))

    return g
