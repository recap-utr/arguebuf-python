import typing as t
from collections.abc import Iterable, Mapping

import pendulum

from arguebuf import dt
from arguebuf.model import Graph, utils
from arguebuf.model.edge import Edge, warn_missing_nodes
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.scheme import aif2scheme, text2scheme
from arguebuf.schemas import aif

from ._config import Config, DefaultConfig

__all__ = ("load_aif",)


def load_aif(
    obj: aif.Graph,
    name: str | None = None,
    config: Config = DefaultConfig,
    reconstruct_dialog: bool = False,
) -> Graph:
    """Generate Graph structure from AIF argument graph file"""
    g = config.GraphClass(name)

    # Preprocess the graph to handle dialogue nodes
    if reconstruct_dialog:
        obj = preprocess_dialog(obj)

    for aif_node in obj["nodes"]:
        node = (
            atom_from_aif(aif_node, config)
            if aif_node["type"] == "I"
            else scheme_from_aif(aif_node, config)
        )

        if node:
            g.add_node(node)

    for aif_edge in obj["edges"]:
        if edge := edge_from_aif(aif_edge, g.nodes, config):
            g.add_edge(edge)

    return g


def atom_from_aif(obj: aif.Node, config: Config) -> AtomNode:
    """Generate AtomNode object from AIF Node object."""
    timestamp = dt.from_format(obj.get("timestamp"), aif.DATE_FORMAT) or pendulum.now()

    return config.AtomNodeClass(
        id=obj["nodeID"],
        metadata=config.MetadataClass(timestamp, timestamp),
        text=utils.parse(obj["text"], config.nlp),
    )


def scheme_from_aif(obj: aif.Node, config: Config) -> SchemeNode | None:
    """Generate SchemeNode object from AIF Node object."""

    aif_type = obj["type"]
    aif_scheme: str = obj.get("scheme", obj["text"])

    if aif_type in aif2scheme:
        scheme = aif2scheme[t.cast(aif.SchemeType, aif_type)]

        # TODO: Handle formatting like capitalization, spaces, underscores, etc.
        # TODO: Araucaria does not use spaces between scheme names
        # aif_scheme = re.sub("([A-Z])", r" \1", aif_scheme)
        if scheme and (found_scheme := text2scheme[type(scheme)].get(aif_scheme)):
            scheme = found_scheme

        timestamp = (
            dt.from_format(obj.get("timestamp"), aif.DATE_FORMAT) or pendulum.now()
        )

        return config.SchemeNodeClass(
            id=obj["nodeID"],
            metadata=config.MetadataClass(timestamp, timestamp),
            scheme=scheme,
        )

    return None


def edge_from_aif(
    obj: aif.Edge, nodes: t.Mapping[str, AbstractNode], config: Config
) -> Edge | None:
    """Generate Edge object from AIF Edge format."""
    source_id = obj.get("fromID")
    target_id = obj.get("toID")

    if source_id in nodes and target_id in nodes:
        return config.EdgeClass(
            id=obj["edgeID"],
            source=nodes[source_id],
            target=nodes[target_id],
        )
    else:
        warn_missing_nodes(obj["edgeID"], source_id, target_id)

    return None


# Node types that are not directly supported in arguebuf
UNSUPPORTED_NODE_TYPES = {"L", "TA", "YA"}


def preprocess_dialog(graph: aif.Graph) -> aif.Graph:
    """Preprocess AIF graph by removing dialogue nodes and reconnecting arguments.

    Removes unsupported dialogue nodes (L, TA, YA) while preserving
    argument structure by creating rephrase connections.
    """
    edges_from: dict[str, list[str]] = {}
    edges_to: dict[str, list[str]] = {}

    for edge in graph["edges"]:
        edges_from.setdefault(edge["fromID"], []).append(edge["toID"])
        edges_to.setdefault(edge["toID"], []).append(edge["fromID"])

    node_types = {n["nodeID"]: n["type"] for n in graph["nodes"]}

    # hanging I-nodes have exactly one incoming edge and no outgoing edges
    hanging_nodes = [
        node_id
        for node_id, node_type in node_types.items()
        if node_type == "I"
        and len(edges_to.get(node_id, [])) == 1
        and node_id not in edges_from
    ]

    result = _remove_dialogue_nodes(graph, node_types)
    _add_rephrase_connections(result, hanging_nodes, edges_to, edges_from, node_types)

    return result


def _edge(from_id: str, to_id: str) -> aif.Edge:
    return {
        "edgeID": utils.uuid(),
        "fromID": from_id,
        "toID": to_id,
        "formEdgeID": None,
    }


def _remove_dialogue_nodes(
    graph: aif.Graph, node_types: Mapping[str, str]
) -> aif.Graph:
    """Remove dialogue nodes (L, TA, YA) and bypass them with direct edges."""
    dialogue_nodes = {
        node_id
        for node_id, node_type in node_types.items()
        if node_type in UNSUPPORTED_NODE_TYPES
    }
    existing_edges = {(e["fromID"], e["toID"]) for e in graph["edges"]}
    incoming: dict[str, list[aif.Edge]] = {}
    outgoing: dict[str, list[aif.Edge]] = {}

    for edge in graph["edges"]:
        incoming.setdefault(edge["toID"], []).append(edge)
        outgoing.setdefault(edge["fromID"], []).append(edge)

    # bypass the dialogue nodes, skipping self-loops and other dialogue nodes
    new_edges = [
        _edge(in_edge["fromID"], out_edge["toID"])
        for node_id in dialogue_nodes
        for in_edge in incoming.get(node_id, [])
        for out_edge in outgoing.get(node_id, [])
        if in_edge["fromID"] != out_edge["toID"]
        and in_edge["fromID"] in node_types
        and out_edge["toID"] in node_types
        and node_types[in_edge["fromID"]] not in UNSUPPORTED_NODE_TYPES
        and node_types[out_edge["toID"]] not in UNSUPPORTED_NODE_TYPES
        and (in_edge["fromID"], out_edge["toID"]) not in existing_edges
    ]

    return {
        "nodes": [n for n in graph["nodes"] if n["nodeID"] not in dialogue_nodes],
        "edges": [
            e
            for e in graph["edges"]
            if e["fromID"] not in dialogue_nodes and e["toID"] not in dialogue_nodes
        ]
        + new_edges,
        "locutions": graph.get("locutions", []),
    }


def _add_rephrase_connections(
    graph: aif.Graph,
    hanging_nodes: Iterable[str],
    edges_to: Mapping[str, list[str]],
    edges_from: Mapping[str, list[str]],
    node_types: Mapping[str, str],
) -> None:
    """Add rephrase nodes to connect hanging nodes to their dialogue partners."""
    nodes = {n["nodeID"]: n for n in graph["nodes"]}
    # pairs that are already connected in any direction
    connected = {frozenset((e["fromID"], e["toID"])) for e in graph["edges"]}

    for hanging_id in hanging_nodes:
        targets = _find_dialogue_targets(hanging_id, edges_to, edges_from, node_types)

        for i, target_id in enumerate(targets):
            pair = frozenset((hanging_id, target_id))

            if target_id not in nodes or pair in connected:
                continue

            rephrase_id = utils.uuid()
            graph["nodes"].append(
                {
                    "nodeID": rephrase_id,
                    "text": "Default Rephrase",
                    "type": "MA",
                    "timestamp": nodes[hanging_id].get("timestamp", ""),
                }
            )

            # the first target is the one being responded to, the others follow
            source_id, sink_id = (
                (target_id, hanging_id)
                if i == 0 and len(targets) > 1
                else (hanging_id, target_id)
            )
            graph["edges"].extend(
                (_edge(source_id, rephrase_id), _edge(rephrase_id, sink_id))
            )
            connected.add(pair)


def _follow(
    node_ids: Iterable[str],
    adjacency: Mapping[str, list[str]],
    node_types: Mapping[str, str],
    node_type: str,
) -> list[str]:
    """Get all neighbors of the given type in the order of the adjacency lists."""
    return [
        neighbor
        for node_id in node_ids
        for neighbor in adjacency.get(node_id, [])
        if node_types.get(neighbor) == node_type
    ]


def _find_dialogue_targets(
    node_id: str,
    edges_to: Mapping[str, list[str]],
    edges_from: Mapping[str, list[str]],
    node_types: Mapping[str, str],
) -> list[str]:
    """Find I-nodes that a hanging node should connect to based on dialogue structure."""
    # the locution that asserts this node via a YA node
    locutions = _follow(
        _follow([node_id], edges_to, node_types, "YA"), edges_to, node_types, "L"
    )

    if not locutions:
        return []

    targets: list[str] = []

    # backward connections (what this responds to) come before forward ones
    for edges in (edges_to, edges_from):
        transitions = _follow(locutions[:1], edges, node_types, "TA")
        partner_locutions = _follow(transitions, edges, node_types, "L")
        assertions = _follow(partner_locutions, edges_from, node_types, "YA")
        targets.extend(
            i_node
            for i_node in _follow(assertions, edges_from, node_types, "I")
            if i_node != node_id
        )

    return targets
