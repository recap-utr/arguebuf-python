import html

from arguebuf.model import GraphView
from arguebuf.model.participant import Participant
from arguebuf.schemas import aif, xaif

from ._dump_aif import dump_edge, dump_node

__all__ = ("dump_participant", "dump_xaif")


def dump_xaif[A, S, E, R, P, N, G](obj: GraphView[A, S, E, R, P, N, G]) -> xaif.Graph:
    """Export structure of Graph instance to xAIF argument graph format.

    xAIF nodes have no timestamps, so they are omitted.
    The resources are joined into an HTML `text` with newlines as `<br>`.
    """
    return {
        "AIF": {
            "nodes": [dump_node(node, timestamp=False) for node in obj.nodes.values()],
            "edges": [dump_edge(edge) for edge in obj.edges.values()],
            "locutions": [],
            "schemefulfillments": [],
            "descriptorfulfillments": [],
            "participants": [
                dump_participant(participant)
                for participant in obj.participants.values()
            ],
        },
        "text": "<br>".join(
            html.escape(resource.text, quote=False).replace("\n", "<br>")
            for resource in obj.resources.values()
        ),
        "dialog": False,
    }


def dump_participant[P](obj: Participant[P]) -> aif.Participant:
    """Export a participant, its name is split at the first space into first name and surname."""
    firstname, _, surname = (obj.name or "").partition(" ")

    return {"participantID": obj.id, "firstname": firstname, "surname": surname}
