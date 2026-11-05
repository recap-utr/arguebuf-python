from typing import Literal, assert_never, overload

from google.protobuf import proto_json

from arguebuf.model import GraphView
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject
from arguebuf.schemas import aif, xaif

from ._dump_aif import dump_aif
from ._dump_protobuf import dump_protobuf
from ._dump_xaif import dump_xaif
from ._format import Format

__all__ = ("dump_dict",)


@overload
def dump_dict[A, S, E, R, P, N, G](
    graph: GraphView[A, S, E, R, P, N, G],
    *,
    format: Literal["aif"],
    codecs: Codecs[A, S, E, R, P, N, G] = ...,
) -> aif.Graph: ...


@overload
def dump_dict[A, S, E, R, P, N, G](
    graph: GraphView[A, S, E, R, P, N, G],
    *,
    format: Literal["xaif"],
    codecs: Codecs[A, S, E, R, P, N, G] = ...,
) -> xaif.Graph: ...


@overload
def dump_dict[A, S, E, R, P, N, G](
    graph: GraphView[A, S, E, R, P, N, G],
    *,
    format: Literal["arguebuf"] = "arguebuf",
    codecs: Codecs[A, S, E, R, P, N, G] = ...,
) -> JsonObject: ...


@overload
def dump_dict[A, S, E, R, P, N, G](
    graph: GraphView[A, S, E, R, P, N, G],
    *,
    format: Format,
    codecs: Codecs[A, S, E, R, P, N, G] = ...,
) -> aif.Graph | xaif.Graph | JsonObject: ...


def dump_dict[A, S, E, R, P, N, G](
    graph: GraphView[A, S, E, R, P, N, G],
    *,
    format: Format = "arguebuf",
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
) -> aif.Graph | xaif.Graph | JsonObject:
    """Export structure of Graph instance to a dict in the given `format`.

    Only the Arguebuf format contains userdata, which is dumped by `codecs`.

    Examples:
        >>> from arguebuf import Graph
        >>> sorted(dump_dict(Graph(), format="aif"))
        ['edges', 'locutions', 'nodes']
    """
    match format:
        case "aif":
            return dump_aif(graph)
        case "xaif":
            return dump_xaif(graph)
        case "arguebuf":
            return proto_json.serialize(dump_protobuf(graph, codecs=codecs))
        case _:
            assert_never(format)
