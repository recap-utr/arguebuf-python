import typing as t

from arg_services.graph.v1 import graph_pb2
from google.protobuf.json_format import MessageToDict

from arguebuf import dt
from arguebuf.model import Graph, utils
from arguebuf.model.edge import Edge, warn_missing_nodes
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.reference import Reference
from arguebuf.model.resource import Resource
from arguebuf.model.scheme import (
    protobuf2attack,
    protobuf2preference,
    protobuf2rephrase,
    protobuf2support,
)

from ._config import Config, DefaultConfig

__all__ = ("load_protobuf",)


def load_protobuf(
    obj: graph_pb2.Graph,
    name: t.Optional[str] = None,
    config: Config = DefaultConfig,
) -> Graph:
    """Generate Graph structure from PROTOBUF argument graph file.(Link?)"""
    g = config.GraphClass(name)

    for resource_id, resource in obj.resources.items():
        g.add_resource(
            config.ResourceClass(
                utils.parse(resource.text, config.nlp),
                resource.title,
                resource.source,
                dt.from_protobuf(resource.timestamp),
                metadata_from_protobuf(resource.metadata, config),
                MessageToDict(resource.userdata),
                resource_id,
            )
        )

    for participant_id, participant in obj.participants.items():
        g.add_participant(
            config.ParticipantClass(
                participant.name,
                participant.username,
                participant.email,
                participant.url,
                participant.location,
                participant.description,
                metadata_from_protobuf(participant.metadata, config),
                MessageToDict(participant.userdata),
                participant_id,
            )
        )

    for analyst_id, analyst in obj.analysts.items():
        g.add_analyst(
            config.AnalystClass(
                analyst.name,
                analyst.email,
                MessageToDict(analyst.userdata),
                analyst_id,
            )
        )

    for node_id, node in obj.nodes.items():
        if node.WhichOneof("type") == "atom":
            g.add_node(
                atom_from_protobuf(node_id, node, g.resources, g.participants, config)
            )
        elif node.WhichOneof("type") == "scheme":
            g.add_node(scheme_from_protobuf(node_id, node, config))
        # TODO: Raise error if node is neither scheme nor atom

    for edge_id, proto_edge in obj.edges.items():
        if edge := edge_from_protobuf(edge_id, proto_edge, g.nodes, config):
            g.add_edge(edge)

    major_claim = g.nodes[obj.major_claim] if obj.major_claim else None

    if major_claim and isinstance(major_claim, AtomNode):
        g._major_claim = major_claim

    g.userdata = MessageToDict(obj.userdata)
    g.metadata = metadata_from_protobuf(obj.metadata, config)
    g.library_version = obj.library_version
    g.schema_version = obj.schema_version

    return g


def atom_from_protobuf(
    id: str,
    obj: graph_pb2.Node,
    resources: t.Mapping[str, Resource],
    participants: t.Mapping[str, Participant],
    config: Config,
) -> AtomNode:
    """Generate AtomNode object from PROTOBUF Node object."""
    return config.AtomNodeClass(
        utils.parse(obj.atom.text, config.nlp),
        reference_from_protobuf(obj.atom.reference, resources, config),
        participants.get(obj.atom.participant),
        metadata_from_protobuf(obj.metadata, config),
        MessageToDict(obj.userdata),
        id=id,
    )


def scheme_from_protobuf(id: str, obj: graph_pb2.Node, config: Config) -> SchemeNode:
    """Generate SchemeNode object from OVA Node object."""

    scheme_type = obj.scheme.WhichOneof("type")
    scheme = None

    if scheme_type is None:
        scheme = None
    elif scheme_type == "support":
        scheme = protobuf2support[obj.scheme.support]
    elif scheme_type == "attack":
        scheme = protobuf2attack[obj.scheme.attack]
    elif scheme_type == "rephrase":
        scheme = protobuf2rephrase[obj.scheme.rephrase]
    elif scheme_type == "preference":
        scheme = protobuf2preference[obj.scheme.preference]

    return config.SchemeNodeClass(
        scheme,
        list(obj.scheme.premise_descriptors),
        metadata_from_protobuf(obj.metadata, config),
        MessageToDict(obj.userdata),
        id=id,
    )


def edge_from_protobuf(
    id: str,
    obj: graph_pb2.Edge,
    nodes: t.Mapping[str, AbstractNode],
    config: Config,
) -> t.Optional[Edge]:
    """Generate Edge object from PROTOBUF Edge format."""
    if obj.source in nodes and obj.target in nodes:
        return config.EdgeClass(
            nodes[obj.source],
            nodes[obj.target],
            metadata_from_protobuf(obj.metadata, config),
            MessageToDict(obj.userdata),
            id=id,
        )
    else:
        warn_missing_nodes(id, obj.source, obj.target)

    return None


def metadata_from_protobuf(obj: graph_pb2.Metadata, config: Config) -> Metadata:
    return config.MetadataClass(
        dt.from_protobuf(obj.created),
        dt.from_protobuf(obj.updated),
        # analysts[obj.analyst]
    )


def reference_from_protobuf(
    obj: graph_pb2.Reference,
    resources: t.Mapping[str, Resource],
    config: Config,
) -> t.Optional[Reference]:
    """Generate Resource object from PROTOBUF format Graph's Resource object."""
    if obj.text:
        if obj.resource:
            return config.ReferenceClass(
                resources[obj.resource],
                obj.offset,
                utils.parse(obj.text, config.nlp),
            )

        else:
            return config.ReferenceClass(
                None,
                None,
                utils.parse(obj.text, config.nlp),
            )

    return None
