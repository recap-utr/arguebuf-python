from arguebuf.model import Graph
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.participant import Participant
from arguebuf.model.resource import Resource
from arguebuf.model.scheme import is_default_scheme, scheme_type2name
from arguebuf.patch._schema import (
    PARTICIPANT_FIELDS,
    AtomPatch,
    Outline,
    ParticipantPatch,
    ResourcePatch,
    SchemePatch,
)

__all__ = ("outline",)


def outline[A, S, E, R, P, N, G](graph: Graph[A, S, E, R, P, N, G]) -> Outline:
    """The graph in the shape of a patch, e.g. to show it to an agent.

    Examples:
        >>> outline(Graph())
        {'resources': [], 'participants': [], 'atoms': [], 'schemes': []}
    """
    result: Outline = {
        "resources": [_resource_outline(item) for item in graph.resources.values()],
        "participants": [
            _participant_outline(item) for item in graph.participants.values()
        ],
        "atoms": [_atom_outline(item) for item in graph.atom_nodes.values()],
        "schemes": [
            _scheme_outline(graph, item) for item in graph.scheme_nodes.values()
        ],
    }

    if graph.major_claim is not None:
        result["majorClaim"] = graph.major_claim

    return result


def _scheme_outline[A, S, E, R, P, N, G](
    graph: Graph[A, S, E, R, P, N, G], scheme: SchemeNode[S]
) -> SchemePatch:
    item: SchemePatch = {"id": scheme.id}
    value = scheme.scheme

    if value is not None:
        item["type"] = scheme_type2name[type(value)]

        if not is_default_scheme(value):
            item["scheme"] = value.value

    item["premises"] = [node.id for node in graph.premise_nodes(scheme)]
    conclusion = next(iter(graph.outgoing_nodes(scheme)), None)

    if conclusion is not None:
        item["conclusion"] = conclusion.id

    return item


def _resource_outline[R](resource: Resource[R]) -> ResourcePatch:
    item: ResourcePatch = {"id": resource.id}

    if resource.title is not None:
        item["title"] = resource.title

    if resource.source is not None:
        item["source"] = resource.source

    return item


def _participant_outline[P](participant: Participant[P]) -> ParticipantPatch:
    item: ParticipantPatch = {"id": participant.id}

    for key in PARTICIPANT_FIELDS:
        if (value := getattr(participant, key)) is not None:
            item[key] = value

    return item


def _atom_outline[A](atom: AtomNode[A]) -> AtomPatch:
    item: AtomPatch = {"id": atom.id, "text": atom.text}

    if atom.reference is not None and atom.reference.resource is not None:
        item["resource"] = atom.reference.resource

    if atom.participant is not None:
        item["participant"] = atom.participant

    return item
