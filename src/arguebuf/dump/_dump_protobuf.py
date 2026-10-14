import importlib.metadata
from datetime import datetime
from typing import cast

from arg_services.graph.v1 import graph_pb2
from google.protobuf.struct_pb2 import Struct
from google.protobuf.timestamp_pb2 import Timestamp

from arguebuf.model import Graph
from arguebuf.model.analyst import Analyst
from arguebuf.model.edge import Edge
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.reference import Reference
from arguebuf.model.resource import Resource
from arguebuf.model.scheme import (
    Attack,
    Preference,
    Rephrase,
    Support,
    attack2protobuf,
    preference2protobuf,
    rephrase2protobuf,
    support2protobuf,
)
from arguebuf.model.userdata import Userdata

__all__ = ("dump_protobuf",)

LIBRARY_VERSION = importlib.metadata.version("arg_services")


# The protobuf runtime converts datetimes and dicts to their well-known types,
# but the generated stubs do not declare these conversions yet.
def _timestamp(value: datetime | None) -> Timestamp | None:
    return cast(Timestamp | None, value)


def _struct(value: Userdata) -> Struct | None:
    # empty userdata is omitted
    return cast(Struct | None, value or None)


def dump_protobuf[T](obj: Graph[T]) -> graph_pb2.Graph:
    """Export structure of Graph instance to protobuf argument graph format."""
    return graph_pb2.Graph(
        schema_version=1,
        library_version=LIBRARY_VERSION,
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(obj.userdata),
        major_claim=obj.major_claim.id if obj.major_claim else None,
        nodes={node_id: node_to_protobuf(node) for node_id, node in obj.nodes.items()},
        edges={edge_id: edge_to_protobuf(edge) for edge_id, edge in obj.edges.items()},
        resources={
            resource_id: resource_to_protobuf(resource)
            for resource_id, resource in obj.resources.items()
        },
        participants={
            participant_id: participant_to_protobuf(participant)
            for participant_id, participant in obj.participants.items()
        },
        analysts={
            analyst_id: analyst_to_protobuf(analyst)
            for analyst_id, analyst in obj.analysts.items()
        },
    )


def node_to_protobuf(obj: AbstractNode) -> graph_pb2.Node:
    match obj:
        case AtomNode():
            return atom_to_protobuf(obj)
        case SchemeNode():
            return scheme_to_protobuf(obj)
        case _:
            raise ValueError("Node type not supported")


def atom_to_protobuf[T](obj: AtomNode[T]) -> graph_pb2.Node:
    """Export AtomNode object into protobuf Node object."""
    return graph_pb2.Node(
        atom=graph_pb2.Atom(
            text=obj.plain_text,
            reference=reference_to_protobuf(obj.reference) if obj.reference else None,
            participant=obj.participant.id if obj.participant else None,
        ),
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(obj.userdata),
    )


def scheme_to_protobuf(obj: SchemeNode) -> graph_pb2.Node:
    """Export SchemeNode object into protobuf Node object."""
    match obj.scheme:
        case Support():
            scheme = graph_pb2.Scheme(support=support2protobuf[obj.scheme])
        case Attack():
            scheme = graph_pb2.Scheme(attack=attack2protobuf[obj.scheme])
        case Rephrase():
            scheme = graph_pb2.Scheme(rephrase=rephrase2protobuf[obj.scheme])
        case Preference():
            scheme = graph_pb2.Scheme(preference=preference2protobuf[obj.scheme])
        case _:
            scheme = graph_pb2.Scheme()

    scheme.premise_descriptors.extend(obj.premise_descriptors)

    return graph_pb2.Node(
        scheme=scheme,
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(obj.userdata),
    )


def analyst_to_protobuf(obj: Analyst) -> graph_pb2.Analyst:
    """Export Analyst object into protobuf format."""
    return graph_pb2.Analyst(
        name=obj.name or "",
        email=obj.email,
        userdata=_struct(obj.userdata),
    )


def edge_to_protobuf(obj: Edge) -> graph_pb2.Edge:
    """Export Edge object into protobuf Edge format."""
    return graph_pb2.Edge(
        source=obj.source.id,
        target=obj.target.id,
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(obj.userdata),
    )


def metadata_to_protobuf(obj: Metadata) -> graph_pb2.Metadata:
    return graph_pb2.Metadata(
        created=_timestamp(obj.created), updated=_timestamp(obj.updated)
    )


def participant_to_protobuf(obj: Participant) -> graph_pb2.Participant:
    """Export Participant object into protobuf format."""
    return graph_pb2.Participant(
        name=obj.name or "",
        username=obj.username,
        email=obj.email,
        url=obj.url,
        location=obj.location,
        description=obj.description,
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(obj.userdata),
    )


def reference_to_protobuf[T](obj: Reference[T]) -> graph_pb2.Reference:
    """Export Reference object into protobuf format."""
    return graph_pb2.Reference(
        text=obj.plain_text,
        resource=obj.resource.id if obj.resource else None,
        offset=obj.offset,
    )


def resource_to_protobuf[T](obj: Resource[T]) -> graph_pb2.Resource:
    """Export Resource object into protobuf format."""
    return graph_pb2.Resource(
        text=obj.plain_text,
        title=obj.title,
        source=obj.source,
        timestamp=_timestamp(obj.timestamp),
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(obj.userdata),
    )
