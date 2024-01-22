from __future__ import annotations
import uuid, datetime

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


class NewNode:
    def __init__(self, node_id, text, node_type, timestamp):
        self.node_id = node_id
        self.text = text
        self.node_type = node_type
        self.timestamp = timestamp
        self.incoming_edges = []
        self.outgoing_edges = []

    def add_incoming_edge(self, edge):
        self.incoming_edges.append(edge)

    def add_outgoing_edge(self, edge):
        self.outgoing_edges.append(edge)

    def __repr__(self):
        return f"Node(node_id={self.node_id}, text={self.text}, type={self.node_type}, timestamp={self.timestamp}, incoming_edges={self.incoming_edges}, outgoing_edges={self.outgoing_edges})"


def get_connected_nodes_of_type(node, node_type, nodes):
    """Returns a list of nodes connected to the given node (either incoming or outgoing) of a specific type."""
    connected_node_ids = [edge['fromID'] for edge in node.incoming_edges] + [edge['toID'] for edge in
                                                                             node.outgoing_edges]
    return [nodes[node_id] for node_id in connected_node_ids if nodes[node_id].node_type == node_type]


# Function to get connected nodes excluding certain types
def get_connected_nodes_excluding_types(node, excluded_types, nodes):
    """Returns a list of nodes connected to the given node (either incoming or outgoing) excluding specific types."""
    connected_node_ids = [edge['fromID'] for edge in node.incoming_edges] + [edge['toID'] for edge in
                                                                             node.outgoing_edges]
    return [nodes[node_id] for node_id in connected_node_ids if nodes[node_id].node_type not in excluded_types]


# Function to check if two nodes are connected
def are_nodes_connected(node1, node2):
    """Returns True if node1 and node2 are connected (either node1 to node2 or node2 to node1), otherwise False."""
    return any(edge['fromID'] == node1.node_id and edge['toID'] == node2.node_id for edge in node1.outgoing_edges) or \
        any(edge['fromID'] == node2.node_id and edge['toID'] == node1.node_id for edge in node2.outgoing_edges)


# Function to generate a unique ID (this is a placeholder, replace with your ID generation logic)
def generate_unique_id():
    return str(uuid.uuid4())


def remove_loops_in_hanging_nodes(hanging_nodes, obj, nodes):
    # Check for and remove loops
    # 1) For each hanging_node take any outgoing edge
    # 2) For each outgoing edge that check what argumentNode it reaches, if its not in the list of hanging_nodes return
    # If it was a hanging_node find the outgoing edge that goes back to the previous hanging_node and delete this path
    """Remove loops formed by hanging nodes."""
    hanging_node_ids = {node.node_id for node in hanging_nodes}

    for hanging_node in hanging_nodes:
        for edge in hanging_node.outgoing_edges:
            target_node_id = edge['toID']

            # Check if the target node is also a hanging node
            if target_node_id in hanging_node_ids:
                # Loop detected, remove the edge and the associated rephrase node
                rephrase_node_id = edge['fromID']

                # Remove the edge and rephrase node from obj
                obj["edges"] = [e for e in obj["edges"] if e["edgeID"] != edge["edgeID"]]
                obj["nodes"] = [n for n in obj["nodes"] if n["nodeID"] != rephrase_node_id]

                # Update the nodes dictionary
                if rephrase_node_id in nodes:
                    del nodes[rephrase_node_id]

                # Update the hanging_node's outgoing edges
                hanging_node.outgoing_edges = [e for e in hanging_node.outgoing_edges if e["edgeID"] != edge["edgeID"]]
                break  # Break after removing the loop for this hanging node


def process_each_hanging_node(hanging_nodes, obj, nodes, updated_hanging_nodes):
    # find and connect plausible connected Nodes near these individually:
    # 1) go back to Dialog-Node, eg "Chris Philp: <text>", via the only connected "Asserting" Node, save the Speakername
    # 2) go to the(two?) directly connected "Default Transition" Nodes (either ingoing or outgoing) and for each of them
    # 3) go to the directly connected Dialog-Node and check if the Speakername is similar
    # 4) if so, go from there to the next connected Node eg "Asserting" or something else, but not "Default Trans."
    # 5) From that eg "Asserting" Node go to another Argument Node, eg "Mrs. X thinks that y is good"
    # 6) Check if this Argument Node has a connection (in/out) from the hanging_node, if not create one

    # 1)
    # Iterate over hanging nodes
    # all generated "Rephrase" Nodes should have the same datetime to filter them out for postprocessing
    similar_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for hanging_node in hanging_nodes:
        # Check if the hanging node has exactly one incoming edge
        if len(hanging_node.incoming_edges) == 1:
            # Get the ID of the connected node (Asserting node)
            asserting_node_id = hanging_node.incoming_edges[0]['fromID']
            asserting_node = nodes.get(asserting_node_id)

            # Ensure the asserting node exists and follow its incoming edge
            if asserting_node and len(asserting_node.incoming_edges) == 1:
                # Get the ID of the next node (should be of type "L")
                l_node_id = asserting_node.incoming_edges[0]['fromID']
                l_node = nodes.get(l_node_id)

                # Check if the node is of type "L" and process the speaker's name
                if l_node and l_node.node_type == "L":
                    speaker_name = l_node.text.split(" :", 1)[0]  # Extracting speaker's name
                    speakerNode = l_node  # Save the original speaker's node
                    # print("\n ########################## \n hanging_nodes Dialog:" + str(l_node) +
                    #      "\n ################# \n")

                    # 2) + 3)
                    # Find connected "Default Transition" nodes of type "TA"
                    default_transition_nodes = get_connected_nodes_of_type(l_node, "TA", nodes)

                    # For each "Default Transition" node, find connected "L" nodes and check if the speaker name is =
                    for dt_node in default_transition_nodes:
                        connected_dialog_nodes = get_connected_nodes_of_type(dt_node, "L", nodes)

                        # Check if the speaker name aligns in the connected "L" nodes,excluding the original speakerNode
                        # For each Dialog-Node, find the next connected nodes excluding types "L" and "TA"
                        for dialog_node in connected_dialog_nodes:
                            if dialog_node.node_id != speakerNode.node_id and dialog_node.text.startswith(
                                    speaker_name + " :"):
                                # 4) + 5)
                                # Find connecting nodes
                                connecting_nodes = get_connected_nodes_excluding_types(dialog_node, ["L", "TA"], nodes)

                                # For each connecting node, find the next Argument-Nodes
                                for connecting_node in connecting_nodes:
                                    argument_nodes = get_connected_nodes_excluding_types(connecting_node, ["L", "TA"],
                                                                                         nodes)
                                    # 6)
                                    for argument_node in argument_nodes:  # datetime für alle gleich
                                        if not are_nodes_connected(hanging_node, argument_node):
                                            new_node_id = generate_unique_id()
                                            new_node = {
                                                "nodeID": new_node_id,
                                                "text": "Default Rephrase",
                                                "type": "MA",
                                                "timestamp": similar_datetime,
                                                "scheme": "Default Rephrase",
                                                "schemeID": "144"
                                            }
                                            obj["nodes"].append(new_node)

                                            # Create edges connecting hanging_node -> new_node and new_node -> ArgumentNode
                                            new_edge_1_id = generate_unique_id()
                                            new_edge_1 = {"edgeID": new_edge_1_id, "fromID": hanging_node.node_id,
                                                          "toID": new_node_id}
                                            obj["edges"].append(new_edge_1)

                                            new_edge_2_id = generate_unique_id()
                                            new_edge_2 = {"edgeID": new_edge_2_id, "fromID": new_node_id,
                                                          "toID": argument_node.node_id}
                                            obj["edges"].append(new_edge_2)
                                            # Update the edges in the copied hanging nodes list
                                            # Find and update the hanging_node and argument_node in updated_hanging_nodes
                                            for node in updated_hanging_nodes:
                                                if node.node_id == hanging_node.node_id:
                                                    node.outgoing_edges.append(new_edge_1)
                                                if node.node_id == argument_node.node_id:
                                                    node.incoming_edges.append(new_edge_2)
    # check for loops:
    remove_loops_in_hanging_nodes(updated_hanging_nodes, obj, nodes)
    return obj


def create_and_process_nodes(obj):
    # ================================
    # create and process simple nodes that will contain all their incoming/outgoing edges
    nodes = {}
    for aif_node in obj["nodes"]:
        node_id = aif_node['nodeID']
        node_text = aif_node.get('text', '')
        node_type = aif_node.get('type', '')
        node_timestamp = aif_node.get('timestamp', '')
        nodes[node_id] = NewNode(node_id, node_text, node_type, node_timestamp)

    # process edges and link them to nodes
    for aif_edge in obj["edges"]:
        edge_id = aif_edge['edgeID']
        from_id = aif_edge['fromID']
        to_id = aif_edge['toID']
        edge_data = {'edgeID': edge_id, 'fromID': from_id, 'toID': to_id}

        if from_id in nodes:
            nodes[from_id].add_outgoing_edge(edge_data)
        if to_id in nodes:
            nodes[to_id].add_incoming_edge(edge_data)
    return nodes


def find_hanging_nodes(nodes):
    # find nodes with no outgoing edges and exactly one incoming edge, and not of type "L"
    # These are all the Nodes that have been left hanging in OVA representation and have no edges in the final graph
    # with the original code, lets name them "hanging_nodes"
    hanging_nodes = [node for node in nodes.values() if
                    len(node.incoming_edges) == 1 and
                    not node.outgoing_edges and
                    node.node_type != "L"]
    return hanging_nodes


def process_hanging_nodes(obj):
    nodes = create_and_process_nodes(obj)
    hanging_nodes = find_hanging_nodes(nodes)
    updated_hanging_nodes = hanging_nodes.copy()
    obj = process_each_hanging_node(hanging_nodes, obj, nodes, updated_hanging_nodes)
    return obj


def load_aif(
        obj: aif.Graph,
        name: t.Optional[str] = None,
        config: Config = DefaultConfig,
) -> Graph:
    """Generate Graph structure from AIF argument graph file
    (reference: http://www.wi2.uni-trier.de/shared/publications/2019_LenzOllingerSahitajBergmann_ICCBR.pdf)

    """
    g = config.GraphClass(name)

    # Process hanging nodes
    obj = process_hanging_nodes(obj)

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


def scheme_from_aif(obj: aif.Node, config: Config) -> t.Optional[SchemeNode]:
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
) -> t.Optional[Edge]:
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
