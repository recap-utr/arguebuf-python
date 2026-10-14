from enum import StrEnum

__all__ = ("EdgeStyle",)


class EdgeStyle(StrEnum):
    BEZIER = "curved"
    STRAIGHT = "line"
    STEP = "ortho"
