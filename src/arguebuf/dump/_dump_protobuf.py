import importlib.metadata

from arg_services.graph.v1 import graph_pb2

from arguebuf.dt import to_protobuf
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

__all__ = ("dump_protobuf",)

LIBRARY_VERSION = importlib.metadata.version("arg_services")


def dump_protobuf[T](obj: Graph[T]) -> graph_pb2.Graph:
    """Export structure of Graph instance to protobuf argument graph format."""
    g = graph_pb2.Graph(
        schema_version=1,
        library_version=LIBRARY_VERSION,
        metadata=metadata_to_protobuf(obj.metadata),
    )

    for node_id, node in obj.nodes.items():
        g.nodes[node_id].CopyFrom(node_to_protobuf(node))

    for edge_id, edge in obj.edges.items():
        g.edges[edge_id].CopyFrom(edge_to_protobuf(edge))

    if obj.major_claim:
        g.major_claim = obj.major_claim.id

    for resource_id, resource in obj.resources.items():
        g.resources[resource_id].CopyFrom(resource_to_protobuf(resource))

    for participant_id, participant in obj.participants.items():
        g.participants[participant_id].CopyFrom(participant_to_protobuf(participant))

    for analyst_id, analyst in obj.analysts.items():
        g.analysts[analyst_id].CopyFrom(analyst_to_protobuf(analyst))

    g.userdata.update(obj.userdata)

    return g


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
    proto = graph_pb2.Node(metadata=metadata_to_protobuf(obj.metadata))
    proto.userdata.update(obj.userdata)

    proto.atom.text = obj.plain_text

    if reference := obj.reference:
        proto.atom.reference.CopyFrom(reference_to_protobuf(reference))

    if participant := obj.participant:
        proto.atom.participant = participant.id

    return proto


def scheme_to_protobuf(obj: SchemeNode) -> graph_pb2.Node:
    """Export SchemeNode object into protobuf Node object."""
    proto = graph_pb2.Node(metadata=metadata_to_protobuf(obj.metadata))
    proto.userdata.update(obj.userdata)

    match obj.scheme:
        case Support():
            proto.scheme.support = support2protobuf[obj.scheme]
        case Attack():
            proto.scheme.attack = attack2protobuf[obj.scheme]
        case Rephrase():
            proto.scheme.rephrase = rephrase2protobuf[obj.scheme]
        case Preference():
            proto.scheme.preference = preference2protobuf[obj.scheme]

    proto.scheme.premise_descriptors.extend(obj.premise_descriptors)

    return proto


def analyst_to_protobuf(obj: Analyst) -> graph_pb2.Analyst:
    """Export Analyst object into a Graph's Analyst object in protobuf format."""
    proto = graph_pb2.Analyst(
        name=obj.name or "",
        email=obj.email or "",
    )
    proto.userdata.update(obj.userdata)

    return proto


def edge_to_protobuf(obj: Edge) -> graph_pb2.Edge:
    """Export Edge object into protobuf Edge format."""
    proto = graph_pb2.Edge(
        source=obj.source.id,
        target=obj.target.id,
        metadata=metadata_to_protobuf(obj.metadata),
    )
    proto.userdata.update(obj.userdata)

    return proto


def metadata_to_protobuf(obj: Metadata) -> graph_pb2.Metadata:
    proto = graph_pb2.Metadata()
    to_protobuf(obj.created, proto.created)
    to_protobuf(obj.updated, proto.updated)

    return proto


def participant_to_protobuf(obj: Participant) -> graph_pb2.Participant:
    """Export Participant object into a Graph's Participant object in protobuf format."""
    proto = graph_pb2.Participant(
        name=obj.name or "",
        username=obj.username or "",
        email=obj.email or "",
        url=obj.url or "",
        location=obj.location or "",
        description=obj.description or "",
        metadata=metadata_to_protobuf(obj.metadata),
    )
    proto.userdata.update(obj.userdata)

    return proto


def reference_to_protobuf[T](obj: Reference[T]) -> graph_pb2.Reference:
    """Export Reference object into protobuf format."""
    proto = graph_pb2.Reference(text=obj.plain_text)

    if resource := obj.resource:
        proto.resource = resource.id

    if offset := obj.offset:
        proto.offset = offset

    return proto


def resource_to_protobuf[T](obj: Resource[T]) -> graph_pb2.Resource:
    """Export Resource object into protobuf format."""
    proto = graph_pb2.Resource(
        text=obj.plain_text, metadata=metadata_to_protobuf(obj.metadata)
    )
    proto.userdata.update(obj.userdata)

    if title := obj.title:
        proto.title = title

    if source := obj.source:
        proto.source = source

    to_protobuf(obj.timestamp, proto.timestamp)

    return proto
