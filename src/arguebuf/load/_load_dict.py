from collections.abc import Mapping
from typing import Any, cast

from arg_services.graph.v1 import graph_pb2
from google.protobuf import proto_json

from arguebuf.model import Graph
from arguebuf.schemas import aif, ova, xaif

from ._config import Config
from ._load_aif import load_aif
from ._load_ova import load_ova
from ._load_protobuf import load_protobuf
from ._load_xaif import load_xaif

__all__ = ("load_dict",)


def load_dict[T = str](
    obj: Mapping[str, Any],
    name: str | None = None,
    config: Config[T] = Config(),
) -> Graph[T]:
    """Generate Graph structure from a dict in the OVA, xAIF, AIF, or arguebuf format."""
    if "AIF" in obj:
        return load_xaif(cast(xaif.Graph, obj), name, config)

    if "analysis" in obj:
        return load_ova(cast(ova.Graph, obj), name, config)

    if "locutions" in obj:
        return load_aif(cast(aif.Graph, obj), name, config)

    return load_protobuf(proto_json.parse(graph_pb2.Graph, dict(obj)), name, config)
