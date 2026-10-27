import json
from typing import TextIO

from arguebuf.model import Graph
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject

from ._dump_dict import dump_dict
from ._format import Format

__all__ = ("dump_json",)


def dump_json[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
](
    graph: Graph[A, S, E, G, R, P, N],
    obj: TextIO,
    *,
    format: Format = Format.ARGUEBUF,
    prettify: bool = True,
    codecs: Codecs[A, S, E, G, R, P, N] = DEFAULT_CODECS,
) -> None:
    """Export structure of Graph instance to JSON argument graph format."""
    json.dump(
        dump_dict(graph, format=format, codecs=codecs),
        obj,
        ensure_ascii=False,
        indent=2 if prettify else None,
    )
