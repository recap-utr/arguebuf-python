import json
from dataclasses import dataclass, field

__all__ = ("D2Edge", "D2Graph", "D2Node", "D2Style")


def _quote(value: str) -> str:
    # d2 double-quoted strings use the same escapes as json
    return json.dumps(value, ensure_ascii=False)


@dataclass(slots=True, frozen=True)
class D2Style:
    font_color: str
    bold: bool
    stroke: str
    stroke_width: int
    fill: str

    def __str__(self) -> str:
        return (
            "{\n"
            f"font-color: {_quote(self.font_color)}\n"
            f"bold: {str(self.bold).lower()}\n"
            f"stroke: {_quote(self.stroke)}\n"
            f"stroke-width: {self.stroke_width}\n"
            f"fill: {_quote(self.fill)}\n"
            "}"
        )


@dataclass(slots=True, frozen=True)
class D2Node:
    id: str
    label: str
    shape: str
    style: D2Style

    def __str__(self) -> str:
        return (
            f"{_quote(self.id)}: {{\n"
            f"label: {_quote(self.label)}\n"
            f"shape: {self.shape}\n"
            f"style: {self.style}\n"
            "}\n"
        )


@dataclass(slots=True, frozen=True)
class D2Edge:
    from_id: str
    to_id: str

    def __str__(self) -> str:
        return f"{_quote(self.from_id)} -> {_quote(self.to_id)}\n"


@dataclass(slots=True)
class D2Graph:
    nodes: list[D2Node] = field(default_factory=list)
    edges: list[D2Edge] = field(default_factory=list)

    def __str__(self) -> str:
        return "".join(map(str, [*self.nodes, *self.edges]))
