from collections.abc import Mapping

from arg_services.graph.v1 import graph_pb2
from google.protobuf.json_format import MessageToDict

from arguebuf.dt import from_protobuf
from arguebuf.model import Graph
from arguebuf.model.edge import Edge
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.reference import Reference
from arguebuf.model.resource import Resource
from arguebuf.model.scheme import (
    Scheme,
    protobuf2attack,
    protobuf2preference,
    protobuf2rephrase,
    protobuf2support,
)

from ._config import Config

__all__ = ("load_protobuf",)


def load_protobuf[T = str](
    obj: graph_pb2.Graph,
    name: str | None = None,
    config: Config[T] = Config(),
) -> Graph[T]:
    """Generate Graph structure from a protobuf message."""
    g = config.graph(name)
    g.metadata = metadata_from_protobuf(obj.metadata, config)
    g.userdata = MessageToDict(obj.userdata)
    g.library_version = obj.library_version
    g.schema_version = obj.schema_version

    for resource_id, resource in obj.resources.items():
        g.add_resource(
            config.ResourceClass(
                config.parse(resource.text),
                title=resource.title,
                source=resource.source,
                timestamp=from_protobuf(resource.timestamp),
                metadata=metadata_from_protobuf(resource.metadata, config),
                userdata=MessageToDict(resource.userdata),
                id=resource_id,
            )
        )

    for participant_id, participant in obj.participants.items():
        g.add_participant(
            config.ParticipantClass(
                participant.name,
                username=participant.username,
                email=participant.email,
                url=participant.url,
                location=participant.location,
                description=participant.description,
                metadata=metadata_from_protobuf(participant.metadata, config),
                userdata=MessageToDict(participant.userdata),
                id=participant_id,
            )
        )

    for analyst_id, analyst in obj.analysts.items():
        g.add_analyst(
            config.AnalystClass(
                analyst.name,
                email=analyst.email,
                userdata=MessageToDict(analyst.userdata),
                id=analyst_id,
            )
        )

    for node_id, node in obj.nodes.items():
        match node.WhichOneof("type"):
            case "atom":
                g.add_node(
                    atom_from_protobuf(
                        node_id, node, g.resources, g.participants, config
                    )
                )
            case "scheme":
                g.add_node(scheme_from_protobuf(node_id, node, config))
            case _:
                raise ValueError(f"Node '{node_id}' is neither an atom nor a scheme.")

    for edge_id, proto_edge in obj.edges.items():
        if edge := edge_from_protobuf(edge_id, proto_edge, g.nodes, config):
            g.add_edge(edge)

    if obj.major_claim in g.atom_nodes:
        g.major_claim = obj.major_claim

    return g


def atom_from_protobuf[T](
    id: str,
    obj: graph_pb2.Node,
    resources: Mapping[str, Resource[T]],
    participants: Mapping[str, Participant],
    config: Config[T],
) -> AtomNode[T]:
    """Generate AtomNode object from protobuf Node object."""
    return config.AtomNodeClass(
        config.parse(obj.atom.text),
        reference=reference_from_protobuf(obj.atom.reference, resources, config),
        participant=participants.get(obj.atom.participant),
        metadata=metadata_from_protobuf(obj.metadata, config),
        userdata=MessageToDict(obj.userdata),
        id=id,
    )


def scheme_from_protobuf[T](
    id: str, obj: graph_pb2.Node, config: Config[T]
) -> SchemeNode:
    """Generate SchemeNode object from protobuf Node object."""
    scheme: Scheme | None = None

    match obj.scheme.WhichOneof("type"):
        case "support":
            scheme = protobuf2support[obj.scheme.support]
        case "attack":
            scheme = protobuf2attack[obj.scheme.attack]
        case "rephrase":
            scheme = protobuf2rephrase[obj.scheme.rephrase]
        case "preference":
            scheme = protobuf2preference[obj.scheme.preference]

    return config.SchemeNodeClass(
        scheme,
        premise_descriptors=list(obj.scheme.premise_descriptors),
        metadata=metadata_from_protobuf(obj.metadata, config),
        userdata=MessageToDict(obj.userdata),
        id=id,
    )


def edge_from_protobuf[T](
    id: str,
    obj: graph_pb2.Edge,
    nodes: Mapping[str, AbstractNode],
    config: Config[T],
) -> Edge | None:
    """Generate Edge object from protobuf Edge format."""
    return config.edge(
        nodes,
        obj.source,
        obj.target,
        id,
        metadata=metadata_from_protobuf(obj.metadata, config),
        userdata=MessageToDict(obj.userdata),
    )


def metadata_from_protobuf[T](obj: graph_pb2.Metadata, config: Config[T]) -> Metadata:
    return config.MetadataClass(
        from_protobuf(obj.created),
        from_protobuf(obj.updated),
    )


def reference_from_protobuf[T](
    obj: graph_pb2.Reference,
    resources: Mapping[str, Resource[T]],
    config: Config[T],
) -> Reference[T] | None:
    """Generate Reference object from protobuf Reference object."""
    if not obj.text:
        return None

    return config.ReferenceClass(
        config.parse(obj.text),
        resource=resources[obj.resource] if obj.resource else None,
        offset=obj.offset if obj.resource else None,
    )
