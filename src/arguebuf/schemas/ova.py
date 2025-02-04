import typing as t

from arguebuf.schemas.aif import NodeType

DATE_FORMAT = "DD/MM/YYYY - HH:mm:ss"
DATE_FORMAT_ANALYSIS = "DD/MM/YYYY"


class Node(t.TypedDict):
    id: int
    x: float
    y: float
    color: str
    text: str
    type: NodeType
    scheme: str
    descriptors: dict[str, int]
    cqdesc: dict[str, t.Any]
    visible: bool
    participantID: str
    w: float
    h: float
    imgurl: str | None
    majorClaim: bool | None
    is_check_worthy: str | None
    source: str | None
    text_begin: list[int] | None
    text_end: list[int] | None
    text_length: list[int] | None
    comment: str | None
    annotator: str | None
    date: str | None


Edge = t.TypedDict(
    "Edge",
    {
        "from": Node,
        "to": Node,
        "visible": bool,
        #
        # Specific to ReCAP OVA
        #
        "annotator": str | None,
        "date": str | None,
    },
)


class Participant(t.TypedDict):
    id: int
    firstname: str
    surname: str


class Analysis(t.TypedDict):
    txt: str
    plain_txt: str | None
    annotatorName: str | None
    documentSource: str | None
    documentTitle: str | None
    ovaVersion: str | None


class Graph(t.TypedDict):
    nodes: list[Node]
    edges: list[Edge]
    participants: list[Participant]
    analysis: Analysis
