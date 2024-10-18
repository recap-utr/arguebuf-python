import typing as t

from arg_services.graph.v1 import graph_pb2
from google.protobuf.json_format import ParseDict

from arguebuf.model import Graph
from arguebuf.schemas import aif, ova

from ._config import Config, DefaultConfig
from ._load_aif import load_aif as load_aif
from ._load_ova import load_ova
from ._load_protobuf import load_protobuf

__all__ = ("load_dict",)


def load_dict(
    obj: t.Mapping[str, t.Any],
    name: t.Optional[str] = None,
    config: Config = DefaultConfig,
) -> Graph:
    """Generate Graph structure from DICT argument graph file(Link?)."""
    if "analysis" in obj:
        return load_ova(t.cast(ova.Graph, obj), name, config)

    if "locutions" in obj:
        return load_aif(t.cast(aif.Graph, obj), name, config)

    return load_protobuf(ParseDict(obj, graph_pb2.Graph()), name, config)
