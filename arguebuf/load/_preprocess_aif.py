from dataclasses import dataclass, field

import pendulum

from arguebuf.model import utils
from arguebuf.schemas import aif


@dataclass(slots=True)
class NewNode:
    node_id: str
    text: str
    node_type: str
    timestamp: str
    incoming_edges: list[aif.Edge] = field(default_factory=list)
    outgoing_edges: list[aif.Edge] = field(default_factory=list)

    def add_incoming_edge(self, edge: aif.Edge):
        self.incoming_edges.append(edge)

    def add_outgoing_edge(self, edge: aif.Edge):
        self.outgoing_edges.append(edge)


def get_connected_nodes_of_type(
    node: NewNode, node_type: str, allnodes: dict[str, NewNode]
) -> list[NewNode]:
    """Returns a list of nodes connected to the given node (either incoming or outgoing) of a specific type."""
    connected_node_ids = [edge["fromID"] for edge in node.incoming_edges] + [
        edge["toID"] for edge in node.outgoing_edges
    ]
    return [
        allnodes[node_id]
        for node_id in connected_node_ids
        if allnodes[node_id].node_type == node_type
    ]


def get_connected_nodes_excluding_types(
    node: NewNode, excluded_types: list[str], allnodes: dict[str, NewNode]
) -> list[NewNode]:
    """Returns a list of nodes connected to the given node (either incoming or outgoing) excluding specific types."""
    connected_node_ids = [edge["fromID"] for edge in node.incoming_edges] + [
        edge["toID"] for edge in node.outgoing_edges
    ]
    return [
        allnodes[node_id]
        for node_id in connected_node_ids
        if allnodes[node_id].node_type not in excluded_types
    ]


def are_nodes_connected(node1: NewNode, node2: NewNode) -> bool:
    """Returns True if node1 and node2 are connected (either node1 to node2 or node2 to node1), otherwise False."""
    return any(
        edge["fromID"] == node1.node_id and edge["toID"] == node2.node_id
        for edge in node1.outgoing_edges
    ) or any(
        edge["fromID"] == node2.node_id and edge["toID"] == node1.node_id
        for edge in node2.outgoing_edges
    )


def remove_loops_in_hanging_nodes(
    hanging_nodes: list[NewNode], obj: aif.Graph, allnodes: dict[str, NewNode]
) -> None:
    """
    Removes loops in the graph that are formed specifically by connecting hanging nodes.
    Steps:
    1) For each hanging node, examine any outgoing edge.
    2) Trace each outgoing edge to its destination argument node.
    If the destination is not in the list of hanging nodes, the function returns without making changes.
    3) If the destination is a hanging node,
    search for and identify any outgoing edge from this node that leads back to the initial hanging node.
    4) Upon finding such a loop, delete the path that forms the loop.

     Loop Structure, 2nd Rephrase Node needs to be removed:
    <HangingNode_1> --<Rephrase>--> <HangingNode_2> --<Rephrase>--> <HangingNode_1>
    """
    hanging_node_ids = {node.node_id for node in hanging_nodes}

    for hanging_node in hanging_nodes:
        for edge in hanging_node.outgoing_edges:
            target_node_id = edge["toID"]

            # Check if the target node is also a hanging node
            if target_node_id in hanging_node_ids:
                # Loop detected, remove the edge and the associated rephrase node
                rephrase_node_id = edge["fromID"]

                # Remove the edge and rephrase node from obj
                obj["edges"] = [
                    e for e in obj["edges"] if e["edgeID"] != edge["edgeID"]
                ]
                obj["nodes"] = [
                    n for n in obj["nodes"] if n["nodeID"] != rephrase_node_id
                ]

                # Update the nodes dictionary
                if rephrase_node_id in allnodes:
                    del allnodes[rephrase_node_id]

                # Update the hanging_node's outgoing edges
                hanging_node.outgoing_edges = [
                    e
                    for e in hanging_node.outgoing_edges
                    if e["edgeID"] != edge["edgeID"]
                ]
                break  # Break after removing the loop for this hanging node


def process_each_hanging_node(
    hanging_nodes: list[NewNode],
    obj: aif.Graph,
    allnodes: dict[str, NewNode],
    updated_hanging_nodes: list[NewNode],
) -> aif.Graph:
    """
    Finds and connects plausible connected Nodes based on specific criteria related to dialogues and transitions.

    The process involves several steps:
    1) Navigate back to a Dialog Node, e.g., "Chris Philp: <text>", through the only connected "Asserting" Node, and save the speaker's name.
    2) Move to the one or two directly connected "Default Transition" Nodes, considering both ingoing and outgoing connections.
    3) For each "Default Transition" Node, navigate to the directly connected Dialog Node and check if the speaker's name is similar.
    4) If the speaker's name matches, proceed from this Dialog Node to the next connected Node (e.g., "Asserting" or another type),
    excluding "Default Transition" Nodes.
    5) From the new node, such as an "Asserting" Node, move to another Argument Node, for example, "Mrs. X thinks that Y is good."
    6) Verify if this Argument Node has a connection (either incoming or outgoing) from the hanging_node. If there is no such connection, create one.

    Rough graph structure example:

                                             ---DefaultTransition--> <DialogNode> ---<Assert>--> <ArgumentNode>
    <HangingNode> <--<Assert>-- <DialogNode>
                                             <--DefaultTransition--- <DialogNode> ---<Assert>--> <ArgumentNode>

    """

    # 1)
    # Iterate over hanging nodes
    # all generated "Rephrase" Nodes should have the same datetime to filter them out for postprocessing
    similar_datetime = pendulum.now().format(aif.DATE_FORMAT)
    for hanging_node in hanging_nodes:
        # Check if the hanging node has exactly one incoming edge
        if len(hanging_node.incoming_edges) == 1:
            # Get the ID of the connected node (Asserting node)
            asserting_node_id = hanging_node.incoming_edges[0]["fromID"]
            asserting_node = allnodes.get(asserting_node_id)

            # Ensure the asserting node exists and follow its incoming edge
            if asserting_node and len(asserting_node.incoming_edges) == 1:
                # Get the ID of the next node (should be of type "L")
                l_node_id = asserting_node.incoming_edges[0]["fromID"]
                l_node = allnodes.get(l_node_id)

                # Check if the node is of type "L" and process the speaker's name
                if l_node and l_node.node_type == "L":
                    speaker_name = l_node.text.split(" :", 1)[
                        0
                    ]  # Extracting speaker's name
                    speakerNode = l_node  # Save the original speaker's node

                    # 2) + 3)
                    # Find connected "Default Transition" nodes of type "TA"
                    default_transition_nodes = get_connected_nodes_of_type(
                        l_node, "TA", allnodes
                    )

                    # For each "Default Transition" node, find connected "L" nodes and check if the speaker name is =
                    for dt_node in default_transition_nodes:
                        connected_dialog_nodes = get_connected_nodes_of_type(
                            dt_node, "L", allnodes
                        )

                        # Check if the speaker name aligns in the connected "L" nodes,excluding the original speakerNode
                        # For each Dialog-Node, find the next connected nodes excluding types "L" and "TA"
                        for dialog_node in connected_dialog_nodes:
                            if (
                                dialog_node.node_id != speakerNode.node_id
                                and dialog_node.text.startswith(speaker_name + " :")
                            ):
                                # 4) + 5)
                                # Find connecting nodes
                                connecting_nodes = get_connected_nodes_excluding_types(
                                    dialog_node, ["L", "TA"], allnodes
                                )

                                # For each connecting node, find the next Argument-Nodes
                                for connecting_node in connecting_nodes:
                                    argument_nodes = (
                                        get_connected_nodes_excluding_types(
                                            connecting_node, ["L", "TA"], allnodes
                                        )
                                    )
                                    # 6)
                                    for (
                                        argument_node
                                    ) in argument_nodes:  # datetime für alle gleich
                                        if not are_nodes_connected(
                                            hanging_node, argument_node
                                        ):
                                            new_node_id = utils.uuid()
                                            new_node: aif.Node = {
                                                "nodeID": new_node_id,
                                                "text": "Default Rephrase",
                                                "type": "MA",
                                                "timestamp": similar_datetime,
                                            }
                                            obj["nodes"].append(new_node)

                                            # Create edges connecting hanging_node -> new_node and new_node -> ArgumentNode
                                            new_edge_1_id = utils.uuid()
                                            new_edge_1: aif.Edge = {
                                                "edgeID": new_edge_1_id,
                                                "fromID": hanging_node.node_id,
                                                "toID": new_node_id,
                                                "formEdgeID": None,
                                            }
                                            obj["edges"].append(new_edge_1)

                                            new_edge_2_id = utils.uuid()
                                            new_edge_2: aif.Edge = {
                                                "edgeID": new_edge_2_id,
                                                "fromID": new_node_id,
                                                "toID": argument_node.node_id,
                                                "formEdgeID": None,
                                            }
                                            obj["edges"].append(new_edge_2)
                                            # Update the edges in the copied hanging nodes list
                                            # Find and update the hanging_node and argument_node in updated_hanging_nodes
                                            for node in updated_hanging_nodes:
                                                if node.node_id == hanging_node.node_id:
                                                    node.outgoing_edges.append(
                                                        new_edge_1
                                                    )
                                                if (
                                                    node.node_id
                                                    == argument_node.node_id
                                                ):
                                                    node.incoming_edges.append(
                                                        new_edge_2
                                                    )
    # check for loops:
    remove_loops_in_hanging_nodes(updated_hanging_nodes, obj, allnodes)
    return obj


def create_and_process_nodes(obj: aif.Graph) -> dict[str, NewNode]:
    """
    creates and processes all Nodes, so they contain every ingoing/outgoing edge
    """
    nodes: dict[str, NewNode] = {}
    for aif_node in obj["nodes"]:
        node_id = aif_node["nodeID"]
        node_text = aif_node.get("text", "")
        node_type = aif_node.get("type", "")
        node_timestamp = aif_node.get("timestamp", "")
        nodes[node_id] = NewNode(node_id, node_text, node_type, node_timestamp)

    # process edges and link them to nodes
    for aif_edge in obj["edges"]:
        edge_id = aif_edge["edgeID"]
        from_id = aif_edge["fromID"]
        to_id = aif_edge["toID"]
        edge_data: aif.Edge = {
            "edgeID": edge_id,
            "fromID": from_id,
            "toID": to_id,
            "formEdgeID": None,
        }

        if from_id in nodes:
            nodes[from_id].add_outgoing_edge(edge_data)
        if to_id in nodes:
            nodes[to_id].add_incoming_edge(edge_data)
    return nodes


def find_hanging_nodes(allnodes: dict[str, NewNode]) -> list[NewNode]:
    """
    Identifies nodes within a graph that have no outgoing edges and exactly one incoming edge, excluding nodes of type "L".
    Returns:
        A list of identified hanging nodes
    """
    hanging_nodes = [
        node
        for node in allnodes.values()
        if len(node.incoming_edges) == 1
        and not node.outgoing_edges
        and node.node_type != "L"
    ]
    return hanging_nodes


def process_hanging_nodes(obj: aif.Graph) -> aif.Graph:
    """
    Finds and connects specific Nodes which aren't connected to other ArgumentNodes yet
    """
    allnodes = create_and_process_nodes(obj)
    hanging_nodes = find_hanging_nodes(allnodes)
    updated_hanging_nodes = hanging_nodes.copy()
    obj = process_each_hanging_node(hanging_nodes, obj, allnodes, updated_hanging_nodes)
    return obj
