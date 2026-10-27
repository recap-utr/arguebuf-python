from collections.abc import Mapping

from arg_services.graph.v1 import graph_pb2
from google.protobuf import proto_json

from arguebuf.dt import from_protobuf
from arguebuf.model import Graph
from arguebuf.model.analyst import Analyst
from arguebuf.model.metadata import Metadata
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.participant import AbstractParticipant, Participant
from arguebuf.model.reference import Reference
from arguebuf.model.resource import AbstractResource, Resource
from arguebuf.model.scheme import Scheme, protobuf2scheme
from arguebuf.model.userdata import DEFAULT_CODECS, Codec, Codecs, JsonObject

from ._helpers import add_edge, lookup, new_reference

__all__ = ("load_protobuf",)


def load_protobuf[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
](
    obj: graph_pb2.Graph,
    name: str | None = None,
    *,
    codecs: Codecs[A, S, E, G, R, P, N] = DEFAULT_CODECS,
) -> Graph[A, S, E, G, R, P, N]:
    """Generate Graph structure from a protobuf message.

    Edges, references, and the major claim pointing to unknown elements
    are skipped with a warning, unknown scheme values raise a `ValueError`.
    """
    g: Graph[A, S, E, G, R, P, N] = Graph(
        name,
        metadata=metadata_from_protobuf(obj.metadata),
        userdata=codecs.graph.validate_python(_userdata(obj)),
    )

    for resource_id, resource in obj.resources.items():
        g.add_resource(resource_from_protobuf(resource_id, resource, codecs.resource))

    for participant_id, participant in obj.participants.items():
        g.add_participant(
            participant_from_protobuf(participant_id, participant, codecs.participant)
        )

    for analyst_id, analyst in obj.analysts.items():
        g.add_analyst(
            Analyst(
                analyst.name or None,
                email=analyst.email or None,
                userdata=codecs.analyst.validate_python(_userdata(analyst)),
                id=analyst_id,
            )
        )

    for node_id, node in obj.nodes.items():
        match node.WhichOneof("type"):
            case "atom":
                g.add_node(
                    atom_from_protobuf(
                        node_id, node, g.resources, g.participants, codecs.atom
                    )
                )
            case "scheme":
                g.add_node(scheme_from_protobuf(node_id, node, codecs.scheme))
            case _:
                raise ValueError(f"Node '{node_id}' is neither an atom nor a scheme.")

    for edge_id, edge in obj.edges.items():
        add_edge(
            g,
            codecs,
            edge.source,
            edge.target,
            edge_id,
            metadata=metadata_from_protobuf(edge.metadata),
            userdata=_userdata(edge),
        )

    if major_claim := lookup(g.atom_nodes, obj.major_claim, "major claim", "the graph"):
        g.major_claim = major_claim

    return g


def _userdata(
    obj: graph_pb2.Graph
    | graph_pb2.Node
    | graph_pb2.Edge
    | graph_pb2.Resource
    | graph_pb2.Participant
    | graph_pb2.Analyst,
) -> JsonObject:
    return proto_json.serialize(obj.userdata)


def resource_from_protobuf[R](
    id: str, obj: graph_pb2.Resource, codec: Codec[R]
) -> Resource[R]:
    """Generate Resource object from protobuf Resource object."""
    return Resource(
        obj.text,
        title=obj.title if obj.HasField("title") else None,
        source=obj.source if obj.HasField("source") else None,
        timestamp=from_protobuf(obj.timestamp) if obj.HasField("timestamp") else None,
        metadata=metadata_from_protobuf(obj.metadata),
        userdata=codec.validate_python(_userdata(obj)),
        id=id,
    )


def participant_from_protobuf[P](
    id: str, obj: graph_pb2.Participant, codec: Codec[P]
) -> Participant[P]:
    """Generate Participant object from protobuf Participant object."""
    return Participant(
        obj.name or None,
        username=obj.username if obj.HasField("username") else None,
        email=obj.email if obj.HasField("email") else None,
        url=obj.url if obj.HasField("url") else None,
        location=obj.location if obj.HasField("location") else None,
        description=obj.description if obj.HasField("description") else None,
        metadata=metadata_from_protobuf(obj.metadata),
        userdata=codec.validate_python(_userdata(obj)),
        id=id,
    )


def atom_from_protobuf[A](
    id: str,
    obj: graph_pb2.Node,
    resources: Mapping[str, AbstractResource],
    participants: Mapping[str, AbstractParticipant],
    codec: Codec[A],
) -> AtomNode[A]:
    """Generate AtomNode object from protobuf Node object."""
    owner = f"atom node '{id}'"

    return AtomNode(
        obj.atom.text,
        reference=reference_from_protobuf(obj.atom.reference, resources, owner)
        if obj.atom.HasField("reference")
        else None,
        participant=lookup(participants, obj.atom.participant, "participant", owner),
        metadata=metadata_from_protobuf(obj.metadata),
        userdata=codec.validate_python(_userdata(obj)),
        id=id,
    )


def scheme_from_protobuf[S](
    id: str, obj: graph_pb2.Node, codec: Codec[S]
) -> SchemeNode[S]:
    """Generate SchemeNode object from protobuf Node object."""
    scheme: Scheme | None = None

    if field := obj.scheme.WhichOneof("type"):
        value: int = getattr(obj.scheme, field)

        if (scheme := protobuf2scheme[field].get(value)) is None:
            raise ValueError(
                f"Scheme node '{id}' has the unknown scheme value {value}."
            )

    return SchemeNode(
        scheme,
        premise_descriptors=list(obj.scheme.premise_descriptors),
        metadata=metadata_from_protobuf(obj.metadata),
        userdata=codec.validate_python(_userdata(obj)),
        id=id,
    )


def metadata_from_protobuf(obj: graph_pb2.Metadata) -> Metadata:
    """Generate Metadata object, missing timestamps default to now."""
    return Metadata(
        from_protobuf(obj.created) if obj.HasField("created") else None,
        from_protobuf(obj.updated) if obj.HasField("updated") else None,
    )


def reference_from_protobuf(
    obj: graph_pb2.Reference, resources: Mapping[str, AbstractResource], owner: str
) -> Reference:
    """Generate Reference object, see `new_reference` for unknown resources."""
    return new_reference(
        obj.text,
        obj.resource,
        obj.offset if obj.HasField("offset") else None,
        resources,
        owner,
    )
