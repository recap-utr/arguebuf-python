

from arguebuf.converters.config import ConverterConfig, DefaultConverter
from arguebuf.converters.from_protobuf import from_protobuf
from arguebuf.converters.to_protobuf import to_protobuf
from arguebuf.models.graph import Graph


def copy(obj: Graph, config: ConverterConfig = DefaultConverter) -> Graph:
    """Contents of Graph instance are copied into new Graph object."""

    return from_protobuf(to_protobuf(obj), obj.name, config)
