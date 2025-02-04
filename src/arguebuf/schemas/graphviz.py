from enum import Enum
from typing import Any

from graphviz import Digraph

GraphvizGraph = Digraph | Any


class EdgeStyle(str, Enum):
    BEZIER = "curved"
    STRAIGHT = "line"
    STEP = "ortho"
