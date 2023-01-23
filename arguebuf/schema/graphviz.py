import typing as t
from enum import Enum

from graphviz import Digraph

GraphvizGraph = t.Union[Digraph, t.Any]


class EdgeStyle(Enum):
    BEZIER = "curved"
    STRAIGHT = "line"
    STEP = "ortho"
