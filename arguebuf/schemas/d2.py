import typing as t


class D2Style:
    def __init__(
        self, font_color: str, bold: bool, stroke: str, stroke_width: int, fill: str
    ):
        self.font_color: str = font_color
        self.bold = bold
        self.stroke = stroke
        self.stroke_width = stroke_width
        self.fill = fill


class D2Node:
    def __init__(self, id: str, label: str, shape: str, style: D2Style):
        self.id = id
        self.label = label
        self.shape = shape
        self.style = style


class D2Edge:
    def __init__(self, from_id: str, to_id: str):
        self.from_id = from_id
        self.to_id = to_id


class D2Graph:
    def __init__(self, nodes: t.List[D2Node], edges: t.List[D2Edge]):
        self.nodes = nodes
        self.edges = edges

    def __str__(self):
        str = ""
        for node in self.nodes:
            str += self.__write_node(node)
        for edge in self.edges:
            str += self.__write_edge(edge)
        return str

    def __write_node(self, node: D2Node) -> str:
        str = ""
        label = node.label.replace('"', '\\"')
        str += node.id + ": {\n"
        str += "label: " + label + "\n"
        str += "shape: " + node.shape + "\n"
        str += "style: " + self.__write_style(node.style) + "\n}\n"
        return str

    def __write_style(self, style: D2Style) -> str:
        str = "{\n"
        str += "font-color: " + '"' + style.font_color + '"' + "\n"
        str += "bold: " + style.bold.__str__() + "\n"
        str += "stroke: " + '"' + style.stroke + '"' + "\n"
        str += "stroke-width: " + style.stroke_width.__str__() + "\n"
        str += "fill: " + '"' + style.fill + '"' + "\n}"
        return str

    def __write_edge(self, edge: D2Edge) -> str:
        str = ""
        str += edge.from_id + " -> " + edge.to_id + "\n"
        return str
