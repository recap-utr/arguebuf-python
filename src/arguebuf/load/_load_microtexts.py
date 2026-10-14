from dataclasses import dataclass
from typing import IO

from lxml import etree

from arguebuf.model import Graph
from arguebuf.model.scheme import Attack, Support
from arguebuf.schemas.microtexts import EdgeType

from ._config import Config

__all__ = ("load_microtexts",)

edge2scheme: dict[EdgeType, Support | Attack] = {
    EdgeType.SUPPORT_DEFAULT: Support.DEFAULT,
    EdgeType.SUPPORT_EXAMPLE: Support.EXAMPLE,
    EdgeType.ATTACK_ATOM: Attack.DEFAULT,
}


@dataclass(slots=True, frozen=True)
class _Edge:
    source: str
    target: str
    type: EdgeType


def _elements(root: etree._Element, query: str) -> list[etree._Element]:
    result = root.xpath(query)
    assert isinstance(result, list)

    return [elem for elem in result if isinstance(elem, etree._Element)]


def _edges(root: etree._Element, *edge_types: EdgeType) -> dict[str, _Edge]:
    condition = " or ".join(f"@type='{edge_type}'" for edge_type in edge_types)

    return {
        str(elem.attrib["id"]): _Edge(
            str(elem.attrib["src"]),
            str(elem.attrib["trg"]),
            EdgeType(str(elem.attrib["type"])),
        )
        for elem in _elements(root, f"//edge[{condition}]")
    }


def load_microtexts[T = str](
    obj: IO[str], name: str | None = None, config: Config[T] = Config()
) -> Graph[T]:
    """Generate Graph structure from a microtexts (arggraph) XML file."""
    root = etree.parse(obj).getroot()
    g = config.graph(name or root.get("id"))
    g.userdata = {"stance": root.get("stance"), "topic": root.get("topic_id")}

    source_tags = {
        str(elem.attrib["id"]): elem for elem in _elements(root, "//edu | //joint")
    }
    adu2source = {
        edge.target: edge.source
        for edge in _edges(root, EdgeType.SEGMENTATION).values()
    }

    for adu in _elements(root, "//adu"):
        if not (adu_id := adu.get("id")):
            continue

        source = source_tags[adu2source[adu_id]]

        if source.text is None:
            continue

        atom = config.AtomNodeClass(config.parse(source.text), id=adu_id)

        if adu_type := adu.get("type"):
            atom.userdata["type"] = adu_type

        g.add_node(atom)

        if source.get("implicit"):
            g.major_claim = atom

    atom_edges = _edges(
        root,
        EdgeType.SUPPORT_DEFAULT,
        EdgeType.SUPPORT_EXAMPLE,
        EdgeType.ATTACK_ATOM,
    )

    for edge_id, edge in atom_edges.items():
        if (source_atom := g.atom_nodes.get(edge.source)) and (
            target_atom := g.atom_nodes.get(edge.target)
        ):
            config.connect(
                g,
                source_atom,
                config.SchemeNodeClass(edge2scheme[edge.type], id=edge_id),
                target_atom,
            )

    # undercutters attack the scheme node of another edge
    for edge_id, edge in _edges(root, EdgeType.ATTACK_SCHEME).items():
        if (target_scheme := g.scheme_nodes.get(edge.target)) and (
            atom_node := g.atom_nodes.get(edge.source)
        ):
            config.connect(
                g,
                atom_node,
                config.SchemeNodeClass(Attack.DEFAULT, id=edge_id),
                target_scheme,
            )

    # additional premises are linked to an existing scheme node
    for edge in _edges(root, EdgeType.ADDITIONAL_SOURCE).values():
        if (scheme_node := g.scheme_nodes.get(edge.target)) and (
            atom_node := g.atom_nodes.get(edge.source)
        ):
            g.add_edge(config.EdgeClass(atom_node, scheme_node))

    return g
