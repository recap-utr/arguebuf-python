import importlib.metadata

from arg_services.graph.v1 import graph_pb2
from google.protobuf.struct_pb2 import Struct

from arguebuf._dt import to_protobuf
from arguebuf.model import GraphView
from arguebuf.model.analyst import Analyst
from arguebuf.model.edge import Edge
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.reference import Reference
from arguebuf.model.resource import Resource
from arguebuf.model.scheme import scheme2protobuf
from arguebuf.model.userdata import DEFAULT_CODECS, Codec, Codecs, JsonObject

__all__ = ("LIBRARY_VERSION", "SCHEMA_VERSION", "dump_protobuf")

LIBRARY_VERSION = f"arguebuf-python:{importlib.metadata.version('arguebuf')}"
SCHEMA_VERSION = 1


def _struct[T](codec: Codec[T], value: T) -> Struct | None:
    # empty userdata is omitted
    if not (data := codec.dump_python(value, mode="json")):
        return None

    struct = Struct()
    struct.update(data)

    return struct


def dump_protobuf[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    graph: GraphView[A, S, E, R, P, N, G],
    *,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
) -> graph_pb2.Graph:
    """Export structure of Graph instance to protobuf argument graph format.

    The userdata of every element is dumped by its codec.
    """
    return graph_pb2.Graph(
        schema_version=SCHEMA_VERSION,
        library_version=LIBRARY_VERSION,
        metadata=metadata_to_protobuf(graph.metadata),
        userdata=_struct(codecs.graph, graph.userdata),
        major_claim=graph.major_claim,
        nodes={
            node_id: atom_to_protobuf(node, codecs.atom)
            if isinstance(node, AtomNode)
            else scheme_to_protobuf(node, codecs.scheme)
            for node_id, node in graph.nodes.items()
        },
        edges={
            edge_id: edge_to_protobuf(edge, codecs.edge)
            for edge_id, edge in graph.edges.items()
        },
        resources={
            resource_id: resource_to_protobuf(resource, codecs.resource)
            for resource_id, resource in graph.resources.items()
        },
        participants={
            participant_id: participant_to_protobuf(participant, codecs.participant)
            for participant_id, participant in graph.participants.items()
        },
        analysts={
            analyst_id: analyst_to_protobuf(analyst, codecs.analyst)
            for analyst_id, analyst in graph.analysts.items()
        },
    )


def atom_to_protobuf[A](obj: AtomNode[A], codec: Codec[A]) -> graph_pb2.Node:
    """Export AtomNode object into protobuf Node object."""
    return graph_pb2.Node(
        atom=graph_pb2.Atom(
            text=obj.text,
            reference=reference_to_protobuf(obj.reference) if obj.reference else None,
            participant=obj.participant,
        ),
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(codec, obj.userdata),
    )


def scheme_to_protobuf[S](obj: SchemeNode[S], codec: Codec[S]) -> graph_pb2.Node:
    """Export SchemeNode object into protobuf Node object."""
    scheme = graph_pb2.Scheme(premise_descriptors=obj.premise_descriptors)

    if obj.scheme is not None:
        field, values = scheme2protobuf[type(obj.scheme)]
        setattr(scheme, field, values[obj.scheme])

    return graph_pb2.Node(
        scheme=scheme,
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(codec, obj.userdata),
    )


def analyst_to_protobuf[N](obj: Analyst[N], codec: Codec[N]) -> graph_pb2.Analyst:
    """Export Analyst object into protobuf format."""
    return graph_pb2.Analyst(
        name=obj.name or "",
        email=obj.email,
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(codec, obj.userdata),
    )


def edge_to_protobuf[E](obj: Edge[E], codec: Codec[E]) -> graph_pb2.Edge:
    """Export Edge object into protobuf Edge format."""
    return graph_pb2.Edge(
        source=obj.source,
        target=obj.target,
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(codec, obj.userdata),
    )


def metadata_to_protobuf(obj: Metadata) -> graph_pb2.Metadata:
    """Export Metadata object into protobuf format in UTC."""
    return graph_pb2.Metadata(
        created=to_protobuf(obj.created), updated=to_protobuf(obj.updated)
    )


def participant_to_protobuf[P](
    obj: Participant[P], codec: Codec[P]
) -> graph_pb2.Participant:
    """Export Participant object into protobuf format."""
    return graph_pb2.Participant(
        name=obj.name or "",
        username=obj.username,
        email=obj.email,
        url=obj.url,
        location=obj.location,
        description=obj.description,
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(codec, obj.userdata),
    )


def reference_to_protobuf(obj: Reference) -> graph_pb2.Reference:
    """Export Reference object into protobuf format."""
    return graph_pb2.Reference(
        text=obj.text,
        resource=obj.resource,
        offset=obj.offset,
    )


def resource_to_protobuf[R](obj: Resource[R], codec: Codec[R]) -> graph_pb2.Resource:
    """Export Resource object into protobuf format."""
    return graph_pb2.Resource(
        text=obj.text,
        title=obj.title,
        source=obj.source,
        timestamp=to_protobuf(obj.timestamp),
        metadata=metadata_to_protobuf(obj.metadata),
        userdata=_struct(codec, obj.userdata),
    )
