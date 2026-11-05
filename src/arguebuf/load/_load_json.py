import json
from typing import TextIO

from arguebuf.model import Graph
from arguebuf.model.issue import Reporter
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject

from ._load_dict import load_dict

__all__ = ("load_json",)


def load_json[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    obj: TextIO,
    *,
    name: str | None = None,
    reconstruct_dialog: bool = False,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, R, P, N, G]:
    """Generate Graph structure from JSON argument graph file.

    See `load_dict`, `reconstruct_dialog` only applies to AIF and xAIF graphs.
    """
    return load_dict(
        json.load(obj), name=name, reconstruct_dialog=reconstruct_dialog, codecs=codecs, on_issue=on_issue, strict=strict
    )
