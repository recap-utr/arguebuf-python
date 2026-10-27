import typing as t

from arguebuf.model.userdata import JsonObject
from arguebuf.schemas.aif import NodeType

__all__ = (
    "DATE_FORMAT",
    "DATE_FORMAT_ANALYSIS",
    "Analysis",
    "Edge",
    "Graph",
    "Node",
    "Participant",
)

DATE_FORMAT = "%d/%m/%Y - %H:%M:%S"
DATE_FORMAT_ANALYSIS = "%d/%m/%Y"


class Node(t.TypedDict):
    id: t.ReadOnly[int]
    x: t.ReadOnly[float]
    y: t.ReadOnly[float]
    color: t.ReadOnly[str]
    text: t.ReadOnly[str]
    type: t.ReadOnly[NodeType]
    scheme: t.ReadOnly[str]
    descriptors: t.ReadOnly[dict[str, int | None]]
    cqdesc: t.ReadOnly[JsonObject]
    visible: t.ReadOnly[bool]
    participantID: t.ReadOnly[str]
    w: t.ReadOnly[float]
    h: t.ReadOnly[float]
    imgurl: t.ReadOnly[str | None]
    #
    # Specific to ReCAP OVA
    #
    majorClaim: t.NotRequired[t.ReadOnly[bool | None]]
    is_check_worthy: t.NotRequired[t.ReadOnly[str | None]]
    source: t.NotRequired[t.ReadOnly[str | None]]
    text_begin: t.NotRequired[t.ReadOnly[list[int] | None]]
    text_end: t.NotRequired[t.ReadOnly[list[int] | None]]
    text_length: t.NotRequired[t.ReadOnly[list[int] | None]]
    comment: t.NotRequired[t.ReadOnly[str | None]]
    annotator: t.NotRequired[t.ReadOnly[str | None]]
    date: t.NotRequired[t.ReadOnly[str | None]]


Edge = t.TypedDict(
    "Edge",
    {
        "from": t.ReadOnly[Node],
        "to": t.ReadOnly[Node],
        "visible": t.ReadOnly[bool],
        #
        # Specific to ReCAP OVA
        #
        "annotator": t.NotRequired[t.ReadOnly[str | None]],
        "date": t.NotRequired[t.ReadOnly[str | None]],
    },
)


class Participant(t.TypedDict):
    id: t.ReadOnly[int]
    firstname: t.ReadOnly[str]
    surname: t.ReadOnly[str]


class Analysis(t.TypedDict):
    txt: t.ReadOnly[str]
    #
    # Specific to ReCAP OVA
    #
    plain_txt: t.NotRequired[t.ReadOnly[str | None]]
    documentDate: t.NotRequired[t.ReadOnly[str | None]]
    annotatorName: t.NotRequired[t.ReadOnly[str | None]]
    documentSource: t.NotRequired[t.ReadOnly[str | None]]
    documentTitle: t.NotRequired[t.ReadOnly[str | None]]
    ovaVersion: t.NotRequired[t.ReadOnly[str | None]]


class Graph(t.TypedDict):
    nodes: t.ReadOnly[list[Node]]
    edges: t.ReadOnly[list[Edge]]
    participants: t.ReadOnly[list[Participant]]
    analysis: t.ReadOnly[Analysis]
