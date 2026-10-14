from collections.abc import Mapping
from datetime import UTC

from arg_services.graph.v1 import graph_pb2
from google.protobuf import proto_json

from arguebuf.dt import now
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
    g.userdata = proto_json.serialize(obj.userdata)
    g.library_version = obj.library_version
    g.schema_version = obj.schema_version

    for resource_id, resource in obj.resources.items():
        g.add_resource(
            config.ResourceClass(
                config.parse(resource.text),
                title=resource.title or None,
                source=resource.source or None,
                timestamp=resource.timestamp.ToDatetime(UTC)
                if resource.HasField("timestamp")
                else None,
                metadata=metadata_from_protobuf(resource.metadata, config),
                userdata=proto_json.serialize(resource.userdata),
                id=resource_id,
            )
        )

    for participant_id, participant in obj.participants.items():
        g.add_participant(
            config.ParticipantClass(
                participant.name or None,
                username=participant.username or None,
                email=participant.email or None,
                url=participant.url or None,
                location=participant.location or None,
                description=participant.description or None,
                metadata=metadata_from_protobuf(participant.metadata, config),
                userdata=proto_json.serialize(participant.userdata),
                id=participant_id,
            )
        )

    for analyst_id, analyst in obj.analysts.items():
        g.add_analyst(
            config.AnalystClass(
                analyst.name or None,
                email=analyst.email or None,
                userdata=proto_json.serialize(analyst.userdata),
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
        reference=reference_from_protobuf(obj.atom.reference, resources, config)
        if obj.atom.HasField("reference")
        else None,
        participant=participants.get(obj.atom.participant),
        metadata=metadata_from_protobuf(obj.metadata, config),
        userdata=proto_json.serialize(obj.userdata),
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
        userdata=proto_json.serialize(obj.userdata),
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
        userdata=proto_json.serialize(obj.userdata),
    )


def metadata_from_protobuf[T](obj: graph_pb2.Metadata, config: Config[T]) -> Metadata:
    return config.MetadataClass(
        obj.created.ToDatetime(UTC) if obj.HasField("created") else now(),
        obj.updated.ToDatetime(UTC) if obj.HasField("updated") else now(),
    )


def reference_from_protobuf[T](
    obj: graph_pb2.Reference,
    resources: Mapping[str, Resource[T]],
    config: Config[T],
) -> Reference[T]:
    """Generate Reference object from protobuf Reference object."""
    return config.ReferenceClass(
        config.parse(obj.text),
        resource=resources[obj.resource] if obj.HasField("resource") else None,
        offset=obj.offset if obj.HasField("offset") else None,
    )
