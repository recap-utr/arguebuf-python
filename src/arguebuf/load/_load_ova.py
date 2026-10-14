from collections.abc import Mapping

from lxml import html

from arguebuf.dt import from_format
from arguebuf.model import Graph
from arguebuf.model.edge import Edge
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.resource import Resource
from arguebuf.model.scheme import aif2scheme, resolve_aif_scheme
from arguebuf.model.utils import uuid
from arguebuf.schemas import ova

from ._config import Config

__all__ = ("load_ova",)


def load_ova[T = str](
    obj: ova.Graph,
    name: str | None = None,
    config: Config[T] = Config(),
) -> Graph[T]:
    """Generate Graph structure from OVA argument graph file (reference: http://ova.uni-trier.de/)."""
    g = config.graph(name)
    analysis = obj["analysis"]
    resource = config.ResourceClass(
        config.parse(analysis.get("plain_txt")),
        title=analysis.get("documentTitle"),
        source=analysis.get("documentSource"),
        timestamp=from_format(analysis.get("documentDate"), ova.DATE_FORMAT_ANALYSIS),
    )
    g.add_resource(resource)

    for participant in obj["participants"]:
        g.add_participant(
            config.ParticipantClass(
                f"{participant['firstname']} {participant['surname']}",
                id=str(participant["id"]),
            )
        )

    if analyst_name := analysis.get("annotatorName"):
        g.add_analyst(config.AnalystClass(analyst_name))

    for ova_node in obj["nodes"]:
        if ova_node.get("type") == "I":
            atom = atom_from_ova(ova_node, config)
            g.add_node(atom)

            if ova_node.get("majorClaim"):
                g.major_claim = atom

        elif scheme := scheme_from_ova(ova_node, config):
            g.add_node(scheme)

    for ova_edge in obj["edges"]:
        if edge := edge_from_ova(ova_edge, g.nodes, config):
            g.add_edge(edge)

    if raw_text := analysis.get("txt"):
        _inject_original_text(raw_text, g.atom_nodes, resource, config)

    return g


def _inject_original_text[T](
    raw_text: str,
    nodes: Mapping[str, AtomNode[T]],
    resource: Resource[T],
    config: Config[T],
) -> None:
    """Set references for all atom nodes highlighted in the raw text."""
    doc = html.fromstring(f"<html><head></head><body>{raw_text}</body></html>")
    text = ""

    if (body := doc.find("body")) is None:
        return

    for elem in body.iter():
        # span elements highlight nodes, their id is prefixed with 'node', e.g. 'node5'
        if elem.tag == "span":
            node_key = str(elem.attrib["id"]).removeprefix("node")

            if node := nodes.get(node_key):
                node.reference = config.ReferenceClass(
                    config.parse(elem.text), resource=resource, offset=len(text)
                )

            text += elem.text or ""

        elif elem.tag == "br":
            text += "\n"

        elif elem.text:
            text += elem.text

        # text after a tag always belongs to the overall text
        if elem.tail:
            text += elem.tail


def edge_from_ova[T](
    obj: ova.Edge, nodes: Mapping[str, AbstractNode], config: Config[T]
) -> Edge | None:
    """Generate Edge object from OVA Edge format."""
    return config.edge(
        nodes,
        str(obj["from"]["id"]),
        str(obj["to"]["id"]),
        uuid(),
        metadata=config.metadata(from_format(obj.get("date"), ova.DATE_FORMAT)),
    )


def scheme_from_ova[T](obj: ova.Node, config: Config[T]) -> SchemeNode | None:
    """Generate SchemeNode object from OVA Node object."""
    if obj["type"] not in aif2scheme:
        return None

    return config.SchemeNodeClass(
        resolve_aif_scheme(obj["type"], obj["text"]),
        premise_descriptors=[
            str(node_id)
            for description, node_id in obj["descriptors"].items()
            if not description.lower().startswith("s_conclusion")
        ],
        metadata=config.metadata(from_format(obj.get("date"), ova.DATE_FORMAT)),
        id=str(obj["id"]),
    )


def atom_from_ova[T](obj: ova.Node, config: Config[T]) -> AtomNode[T]:
    """Generate AtomNode object from OVA Node object."""
    return config.AtomNodeClass(
        config.parse(obj["text"]),
        metadata=config.metadata(from_format(obj.get("date"), ova.DATE_FORMAT)),
        id=str(obj["id"]),
    )
