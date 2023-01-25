import typing as t

import pendulum
from lxml import html

from arguebuf.converters.config import ConverterConfig, DefaultConverter
from arguebuf.models.analyst import Analyst
from arguebuf.models.edge import Edge, warn_missing_nodes
from arguebuf.models.graph import Graph
from arguebuf.models.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.models.resource import Resource
from arguebuf.models.scheme import aif2scheme, text2scheme
from arguebuf.schemas import aif, ova
from arguebuf.services import dt, utils


def from_ova(
    obj: ova.Graph,
    name: t.Optional[str] = None,
    config: ConverterConfig = DefaultConverter,
) -> Graph:
    """Generate Graph structure from OVA argument graph file (reference: http://ova.uni-trier.de/)."""
    g = config.GraphClass(name)

    analysis = obj["analysis"]
    resource = config.ResourceClass(
        utils.parse(analysis.get("plain_txt"), config.nlp),
        analysis.get("documentTitle"),
        analysis.get("documentSource"),
        dt.from_format(analysis.get("documentDate"), ova.DATE_FORMAT_ANALYSIS),
    )
    g.add_resource(resource)

    for participant in obj["participants"]:
        g.add_participant(
            config.ParticipantClass(
                name=f"{participant['firstname']} {participant['surname']}",
                id=str(participant["id"]),
            )
        )

    if analyst_name := obj["analysis"].get("annotatorName"):
        g.add_analyst(Analyst(name=analyst_name))

    for ova_node in obj["nodes"]:
        node = (
            atom_from_ova(ova_node, config)
            if ova_node.get("type") == "I"
            else scheme_from_ova(ova_node, config)
        )

        if node:
            g.add_node(node)

        if ova_node.get("major_claim") and isinstance(node, AtomNode):
            g._major_claim = node

    for ova_edge in obj["edges"]:
        if edge := edge_from_ova(ova_edge, g.nodes, config):
            g.add_edge(edge)

    if (analysis := obj.get("analysis")) and (raw_text := analysis.get("txt")):
        _inject_original_text(raw_text, g._atom_nodes, resource, config)

    return g


def _inject_original_text(
    raw_text: str,
    nodes: t.Mapping[str, AtomNode],
    resource: Resource,
    config: ConverterConfig,
) -> None:
    doc = html.fromstring(f"<html><head></head><body>{raw_text}</body></html>")
    text = ""
    body = doc.find("body")

    if body is not None:
        for elem in body.iter():
            # Span elements need special handling
            if elem.tag == "span":
                # The id is prefixed with 'node', e.g. 'node5'.
                node_key = str(elem.attrib["id"]).replace("node", "")
                if node := nodes.get(node_key):
                    node._reference = config.ReferenceClass(
                        resource, len(text), utils.parse(elem.text, config.nlp)
                    )

                if elem.text:
                    text += elem.text

            elif elem.tag == "br":
                text += "\n"

            elif elem.text:
                text += elem.text

            # Text after a tag should always be added to the overall text
            if elem.tail:
                text += elem.tail


def edge_from_ova(
    obj: ova.Edge, nodes: t.Mapping[str, AbstractNode], config: ConverterConfig
) -> t.Optional[Edge]:
    """Generate Edge object from OVA Edge format."""
    source_id = str(obj["from"]["id"])
    target_id = str(obj["to"]["id"])
    date = dt.from_format(obj.get("date"), ova.DATE_FORMAT) or pendulum.now()

    if source_id in nodes and target_id in nodes:
        return config.EdgeClass(
            id=utils.uuid(),
            source=nodes[source_id],
            target=nodes[target_id],
            metadata=config.MetadataClass(date, date),
        )
    else:
        warn_missing_nodes(None, source_id, target_id)

    return None


def scheme_from_ova(obj: ova.Node, config: ConverterConfig) -> t.Optional[SchemeNode]:
    """Generate SchemeNode object from OVA Node object."""

    ova_type = obj["type"]
    ova_scheme = obj["text"]

    if ova_type in aif2scheme:
        scheme = aif2scheme[t.cast(aif.SchemeType, ova_type)]

        if scheme and (found_scheme := text2scheme[type(scheme)].get(ova_scheme)):
            scheme = found_scheme

        premise_descriptors = [
            str(node_id)
            for description, node_id in obj["descriptors"].items()
            if not description.lower().startswith("s_conclusion")
        ]

        timestamp = dt.from_format(obj.get("date"), ova.DATE_FORMAT) or pendulum.now()

        return config.SchemeNodeClass(
            id=str(obj["id"]),
            metadata=config.MetadataClass(timestamp, timestamp),
            scheme=scheme,
            premise_descriptors=premise_descriptors,
        )

    return None


def atom_from_ova(obj: ova.Node, config: ConverterConfig) -> AtomNode:
    """Generate AtomNode object from OVA Node object."""
    timestamp = dt.from_format(obj.get("date"), ova.DATE_FORMAT) or pendulum.now()

    return config.AtomNodeClass(
        id=str(obj["id"]),
        metadata=config.MetadataClass(timestamp, timestamp),
        text=utils.parse(obj["text"], config.nlp),
    )
