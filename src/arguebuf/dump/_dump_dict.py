from typing import assert_never

from google.protobuf import proto_json

from arguebuf.model import Graph
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject

from ._dump_aif import dump_aif
from ._dump_protobuf import dump_protobuf
from ._dump_xaif import dump_xaif
from ._format import Format

__all__ = ("dump_dict",)


def dump_dict[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    graph: Graph[A, S, E, R, P, N, G],
    *,
    format: Format = Format.ARGUEBUF,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
) -> dict[str, object]:
    """Export structure of Graph instance to a dict in the given `format`.

    Only the Arguebuf format contains userdata, which is dumped by `codecs`.
    """
    match format:
        case Format.AIF:
            return dict(dump_aif(graph))
        case Format.XAIF:
            return dict(dump_xaif(graph))
        case Format.ARGUEBUF:
            return proto_json.serialize(dump_protobuf(graph, codecs=codecs))
        case _:
            assert_never(format)
