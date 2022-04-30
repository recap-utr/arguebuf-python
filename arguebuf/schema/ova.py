import typing as t

from arguebuf.schema.aif import NodeType

DATE_FORMAT = "DD/MM/YYYY - HH:mm:ss"
DATE_FORMAT_ANALYSIS = "DD/MM/YYYY"

Node = t.TypedDict(
    "Node",
    {
        "id": int,
        "x": float,
        "y": float,
        "color": str,
        "text": str,
        "type": NodeType,
        "scheme": str,
        "descriptors": t.Dict[str, int],
        "cqdesc": t.Dict[str, t.Any],
        "visible": bool,
        "participantID": str,
        "w": float,
        "h": float,
        #
        # Specific to original OVA
        #
        "imgurl": t.Optional[str],
        #
        # Specific to ReCAP OVA
        #
        "majorClaim": t.Optional[bool],
        "is_check_worthy": t.Optional[str],
        "source": t.Optional[str],
        "text_begin": t.Optional[t.List[int]],
        "text_end": t.Optional[t.List[int]],
        "text_length": t.Optional[t.List[int]],
        "comment": t.Optional[str],
        "annotator": t.Optional[str],
        "date": t.Optional[str],
    },
)

Edge = t.TypedDict(
    "Edge",
    {
        "from": Node,
        "to": Node,
        "visible": bool,
        #
        # Specific to ReCAP OVA
        #
        "annotator": t.Optional[str],
        "date": t.Optional[str],
    },
)

Participant = t.TypedDict("Participant", {"id": int, "firstname": str, "surname": str})

Analysis = t.TypedDict(
    "Analysis",
    {
        "txt": str,
        #
        # Specific to ReCAP OVA
        #
        "plain_txt": t.Optional[str],
        "annotatorName": t.Optional[str],
        "documentSource": t.Optional[str],
        "documentTitle": t.Optional[str],
        "ovaVersion": t.Optional[str],
    },
)

Graph = t.TypedDict(
    "Graph",
    {
        "nodes": t.List[Node],
        "edges": t.List[Edge],
        "participants": t.List[Participant],
        "analysis": Analysis,
    },
)
