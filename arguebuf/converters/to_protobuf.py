from __future__ import annotations

import importlib.metadata

from arg_services.graph.v1 import graph_pb2

from arguebuf.models.analyst import Analyst
from arguebuf.models.edge import Edge
from arguebuf.models.graph import Graph
from arguebuf.models.metadata import Metadata
from arguebuf.models.node import AbstractNode, AtomNode, SchemeNode
from arguebuf.models.participant import Participant
from arguebuf.models.reference import Reference
from arguebuf.models.resource import Resource
from arguebuf.models.scheme import (
    Attack,
    Preference,
    Rephrase,
    Support,
    attack2protobuf,
    preference2protobuf,
    rephrase2protobuf,
    support2protobuf,
)
from arguebuf.services import dt


def to_protobuf(obj: Graph) -> graph_pb2.Graph:
    """Export structure of Graph instance to PROTOBUF argument graph format."""
    try:
        version = importlib.metadata.version("arg_services")
    except importlib.metadata.PackageNotFoundError:
        version = ""

    g = graph_pb2.Graph(
        schema_version=1,
        library_version=version,
        metadata=metadata_to_protobuf(obj.metadata),
    )

    for node_id, node in obj._nodes.items():
        g.nodes[node_id].CopyFrom(node_to_protobuf(node))

    for edge_id, edge in obj._edges.items():
        g.edges[edge_id].CopyFrom(edge_to_protobuf(edge))

    if obj._major_claim:
        g.major_claim = obj._major_claim.id

    for resource_id, resource in obj._resources.items():
        g.resources[resource_id].CopyFrom(resource_to_protobuf(resource))

    for participant_id, participant in obj._participants.items():
        g.participants[participant_id].CopyFrom(participant_to_protobuf(participant))

    for analyst_id, analyst in obj._analysts.items():
        g.analysts[analyst_id].CopyFrom(analyst_to_protobuf(analyst))

    g.userdata.update(obj.userdata)

    return g


def node_to_protobuf(obj: AbstractNode) -> graph_pb2.Node:
    if isinstance(obj, AtomNode):
        return atom_to_protobuf(obj)
    elif isinstance(obj, SchemeNode):
        return scheme_to_protobuf(obj)

    raise ValueError("Node type not supported")


def atom_to_protobuf(obj: AtomNode) -> graph_pb2.Node:
    """Export AtomNode object into PROTOBUF Node object."""
    proto = graph_pb2.Node(metadata=metadata_to_protobuf(obj.metadata))
    proto.userdata.update(obj.userdata)

    proto.atom.text = obj.plain_text

    if reference := obj.reference:
        proto.atom.reference.CopyFrom(reference_to_protobuf(reference))

    if participant := obj.participant:
        proto.atom.participant = participant.id

    return proto


def scheme_to_protobuf(obj: SchemeNode) -> graph_pb2.Node:
    """Export SchemeNode object into PROTOBUF Node object."""
    proto = graph_pb2.Node(metadata=metadata_to_protobuf(obj.metadata))
    proto.userdata.update(obj.userdata)

    if isinstance(obj.scheme, Support):
        proto.scheme.support = support2protobuf[obj.scheme]
    elif isinstance(obj.scheme, Attack):
        proto.scheme.attack = attack2protobuf[obj.scheme]
    elif isinstance(obj.scheme, Rephrase):
        proto.scheme.rephrase = rephrase2protobuf[obj.scheme]
    elif isinstance(obj.scheme, Preference):
        proto.scheme.preference = preference2protobuf[obj.scheme]

    proto.scheme.premise_descriptors.extend(obj.premise_descriptors)

    return proto


def analyst_to_protobuf(obj: Analyst) -> graph_pb2.Analyst:
    """Export Analyst object into a Graph's Analyst object in PROTOBUF format."""
    proto = graph_pb2.Analyst(
        name=obj.name or "",
        email=obj.email or "",
    )
    proto.userdata.update(obj.userdata)

    return proto


def edge_to_protobuf(obj: Edge) -> graph_pb2.Edge:
    """Export Edge object into PROTOBUF Edge format."""
    proto = graph_pb2.Edge(
        source=obj.source.id,
        target=obj.target.id,
        metadata=metadata_to_protobuf(obj.metadata),
    )
    proto.userdata.update(obj.userdata)

    return proto


def metadata_to_protobuf(obj: Metadata) -> graph_pb2.Metadata:
    proto = graph_pb2.Metadata()

    # if analyst := obj._analyst:
    #     proto.analyst = analyst.id

    dt.to_protobuf(obj.created, proto.created)
    dt.to_protobuf(obj.updated, proto.updated)

    return proto


def participant_to_protobuf(obj: Participant) -> graph_pb2.Participant:
    """Export Participant object into a Graph's Participant object in PROTOBUF format."""
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


def reference_to_protobuf(obj: Reference) -> graph_pb2.Reference:
    """Export Resource object into a Graph's Resource object in PROTOBUF format."""
    proto = graph_pb2.Reference(text=obj.plain_text)

    if resource := obj._resource:
        proto.resource = resource.id

    if offset := obj.offset:
        proto.offset = offset

    return proto


def resource_to_protobuf(obj: Resource) -> graph_pb2.Resource:
    """Export Resource object into a Graph's Resource object in PROTOBUF format."""
    proto = graph_pb2.Resource(
        text=obj.plain_text, metadata=metadata_to_protobuf(obj.metadata)
    )
    proto.userdata.update(obj.userdata)

    if title := obj.title:
        proto.title = title

    if source := obj.source:
        proto.source = source

    return proto
