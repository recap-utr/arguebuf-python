from google.protobuf import proto_json

from arguebuf.model import Graph

from ._config import Config, DefaultConfig, Format
from ._dump_aif import dump_aif
from ._dump_protobuf import dump_protobuf
from ._dump_xaif import dump_xaif

__all__ = ("dump_dict",)


def dump_dict[T](graph: Graph[T], config: Config = DefaultConfig) -> dict[str, object]:
    """Export structure of Graph instance to a dict in the configured format."""
    match config.format:
        case Format.AIF:
            return dict(dump_aif(graph))
        case Format.XAIF:
            return dict(dump_xaif(graph))
        case Format.ARGUEBUF:
            return proto_json.serialize(dump_protobuf(graph))
