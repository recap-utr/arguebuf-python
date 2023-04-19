import typing as t


class D2Style(t.TypedDict):
    font_color: str
    bold: str
    stroke: str
    stroke_width: str
    fill: str


class D2Node(t.TypedDict):
    id: str
    label: str
    shape: str
    style: D2Style


class D2Edge(t.TypedDict):
    from_id: str
    to_id: str


class D2Graph(t.TypedDict):
    nodes: t.List[D2Node]
    edges: t.List[D2Edge]
