from arguebuf.model import GraphView
from arguebuf.model.scheme import SCHEME_TYPE_NAMES, is_default_scheme
from arguebuf.patch._schema import (
    AtomPatch,
    Outline,
    ParticipantPatch,
    ResourceOutline,
    SchemeOutline,
)

__all__ = ("outline",)


def outline[A, S, E, R, P, N, G](graph: GraphView[A, S, E, R, P, N, G]) -> Outline:
    """The graph in the shape of a patch, e.g. to show it to an agent.

    Examples:
        >>> from arguebuf import Graph
        >>> outline(Graph()).model_dump()
        {'resources': (), 'participants': (), 'atoms': (), 'schemes': (), 'majorClaim': None}
    """
    return Outline(
        resources=tuple(
            ResourceOutline.model_validate(item, from_attributes=True)
            for item in graph.resources.values()
        ),
        participants=tuple(
            ParticipantPatch.model_validate(item, from_attributes=True)
            for item in graph.participants.values()
        ),
        atoms=tuple(
            AtomPatch(
                id=item.id,
                text=item.text,
                resource=item.reference.resource if item.reference else None,
                participant=item.participant,
            )
            for item in graph.atom_nodes.values()
        ),
        schemes=tuple(
            SchemeOutline(
                id=item.id,
                type=SCHEME_TYPE_NAMES[type(item.scheme)] if item.scheme else None,
                scheme=None
                if item.scheme is None or is_default_scheme(item.scheme)
                else item.scheme.value,
                premises=tuple(node.id for node in graph.premise_nodes(item)),
                conclusion=next((node.id for node in graph.outgoing_nodes(item)), None),
            )
            for item in graph.scheme_nodes.values()
        ),
        major_claim=graph.major_claim,
    )
