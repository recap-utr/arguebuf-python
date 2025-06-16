import typing as t

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
    # Copy the graph
    result: aif.Graph = {
        "nodes": graph["nodes"].copy(),
        "edges": graph["edges"].copy(),
        "locutions": graph.get("locutions", []).copy(),
    }

    # Find hanging nodes before removing dialogue nodes
    hanging_nodes = _find_hanging_nodes(result)

    # Remove dialogue nodes and create bypass edges
    result = _remove_dialogue_nodes(result)

    # Reconnect hanging nodes with rephrase nodes
    result = _add_rephrase_connections(result, hanging_nodes, graph)

    return result


def _find_hanging_nodes(graph: aif.Graph) -> set[str]:
    """Find I-nodes with exactly one incoming edge and no outgoing edges."""
    hanging = set()

    for node in graph["nodes"]:
        if node["type"] != "I":
            continue

        node_id = node["nodeID"]
        incoming = sum(1 for e in graph["edges"] if e["toID"] == node_id)
        outgoing = sum(1 for e in graph["edges"] if e["fromID"] == node_id)

        if incoming == 1 and outgoing == 0:
            hanging.add(node_id)

    return hanging


def _remove_dialogue_nodes(graph: aif.Graph) -> aif.Graph:
    """Remove dialogue nodes (L, TA, YA) and bypass them with direct edges."""
    # Identify dialogue nodes
    dialogue_nodes = {
        n["nodeID"] for n in graph["nodes"] if n["type"] in UNSUPPORTED_NODE_TYPES
    }

    # Find edges to bypass
    new_edges = []
    edges_to_remove = set()

    for node_id in dialogue_nodes:
        incoming = [e for e in graph["edges"] if e["toID"] == node_id]
        outgoing = [e for e in graph["edges"] if e["fromID"] == node_id]

        # Mark these edges for removal
        for edge in incoming + outgoing:
            edges_to_remove.add(edge["edgeID"])

        # Create bypass edges
        for in_edge in incoming:
            for out_edge in outgoing:
                from_id = in_edge["fromID"]
                to_id = out_edge["toID"]

                # Skip self-loops and edges to other dialogue nodes
                if from_id == to_id:
                    continue

                from_node = next(
                    (n for n in graph["nodes"] if n["nodeID"] == from_id), None
                )
                to_node = next(
                    (n for n in graph["nodes"] if n["nodeID"] == to_id), None
                )

                if (
                    from_node
                    and to_node
                    and from_node["type"] not in UNSUPPORTED_NODE_TYPES
                    and to_node["type"] not in UNSUPPORTED_NODE_TYPES
                ):
                    # Check if edge already exists
                    if not any(
                        e["fromID"] == from_id and e["toID"] == to_id
                        for e in graph["edges"]
                    ):
                        new_edges.append(
                            {
                                "edgeID": utils.uuid(),
                                "fromID": from_id,
                                "toID": to_id,
                                "formEdgeID": None,
                            }
                        )

    # Update graph
    graph["nodes"] = [n for n in graph["nodes"] if n["nodeID"] not in dialogue_nodes]
    graph["edges"] = [e for e in graph["edges"] if e["edgeID"] not in edges_to_remove]
    graph["edges"].extend(new_edges)

    return graph


def _add_rephrase_connections(
    graph: aif.Graph, hanging_nodes: set[str], original_graph: aif.Graph
) -> aif.Graph:
    """Add rephrase nodes to connect hanging nodes to their dialogue partners."""
    if not hanging_nodes:
        return graph

    # Build maps for the original graph
    orig_edges_from = {}
    orig_edges_to = {}
    for edge in original_graph["edges"]:
        orig_edges_from.setdefault(edge["fromID"], []).append(edge["toID"])
        orig_edges_to.setdefault(edge["toID"], []).append(edge["fromID"])

    nodes_by_id = {n["nodeID"]: n for n in original_graph["nodes"]}

    new_nodes = []
    new_edges = []
    connections_made = set()

    for hanging_id in hanging_nodes:
        # Find the I-nodes this hanging node should connect to
        targets = _find_dialogue_targets(
            hanging_id, orig_edges_to, orig_edges_from, nodes_by_id
        )

        for i, target_id in enumerate(targets):
            # Skip if target doesn't exist in processed graph
            if not any(n["nodeID"] == target_id for n in graph["nodes"]):
                continue

            # Skip if already connected
            pair = (min(hanging_id, target_id), max(hanging_id, target_id))
            if pair in connections_made:
                continue

            # Check if already connected in the processed graph
            if any(
                (e["fromID"] == hanging_id and e["toID"] == target_id)
                or (e["fromID"] == target_id and e["toID"] == hanging_id)
                for e in graph["edges"]
            ):
                continue

            # Create rephrase node
            rephrase_id = utils.uuid()
            hanging_node = next(n for n in graph["nodes"] if n["nodeID"] == hanging_id)
            new_nodes.append(
                {
                    "nodeID": rephrase_id,
                    "text": "Default Rephrase",
                    "type": "MA",
                    "timestamp": hanging_node.get("timestamp", ""),
                }
            )

            # First target is backward (response), others are forward
            if i == 0 and len(targets) > 1:
                # Backward: target -> rephrase -> hanging
                new_edges.extend(
                    [
                        {
                            "edgeID": utils.uuid(),
                            "fromID": target_id,
                            "toID": rephrase_id,
                            "formEdgeID": None,
                        },
                        {
                            "edgeID": utils.uuid(),
                            "fromID": rephrase_id,
                            "toID": hanging_id,
                            "formEdgeID": None,
                        },
                    ]
                )
            else:
                # Forward: hanging -> rephrase -> target
                new_edges.extend(
                    [
                        {
                            "edgeID": utils.uuid(),
                            "fromID": hanging_id,
                            "toID": rephrase_id,
                            "formEdgeID": None,
                        },
                        {
                            "edgeID": utils.uuid(),
                            "fromID": rephrase_id,
                            "toID": target_id,
                            "formEdgeID": None,
                        },
                    ]
                )

            connections_made.add(pair)

    graph["nodes"].extend(new_nodes)
    graph["edges"].extend(new_edges)

    return graph


def _find_dialogue_targets(
    node_id: str, edges_to: dict, edges_from: dict, nodes_by_id: dict
) -> list[str]:
    """Find I-nodes that a hanging node should connect to based on dialogue structure."""
    targets = []

    # Find the locution that supports this node through YA
    locution = None
    for ya_id in edges_to.get(node_id, []):
        if nodes_by_id.get(ya_id, {}).get("type") == "YA":
            for loc_id in edges_to.get(ya_id, []):
                if nodes_by_id.get(loc_id, {}).get("type") == "L":
                    locution = loc_id
                    break
            if locution:
                break

    if not locution:
        return targets

    # Find backward connections (what this responds to)
    for ta_id in edges_to.get(locution, []):
        if nodes_by_id.get(ta_id, {}).get("type") == "TA":
            for source_loc in edges_to.get(ta_id, []):
                if nodes_by_id.get(source_loc, {}).get("type") == "L":
                    # Find I-nodes from this locution
                    for ya_id in edges_from.get(source_loc, []):
                        if nodes_by_id.get(ya_id, {}).get("type") == "YA":
                            for i_id in edges_from.get(ya_id, []):
                                if (
                                    nodes_by_id.get(i_id, {}).get("type") == "I"
                                    and i_id != node_id
                                ):
                                    targets.append(i_id)

    # Find forward connections (where this transitions to)
    for ta_id in edges_from.get(locution, []):
        if nodes_by_id.get(ta_id, {}).get("type") == "TA":
            for target_loc in edges_from.get(ta_id, []):
                if nodes_by_id.get(target_loc, {}).get("type") == "L":
                    # Find I-nodes from this locution
                    for ya_id in edges_from.get(target_loc, []):
                        if nodes_by_id.get(ya_id, {}).get("type") == "YA":
                            for i_id in edges_from.get(ya_id, []):
                                if (
                                    nodes_by_id.get(i_id, {}).get("type") == "I"
                                    and i_id != node_id
                                ):
                                    targets.append(i_id)

    return targets
