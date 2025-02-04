from arguebuf.dump import protobuf as dump_protobuf
from arguebuf.load import protobuf as load_protobuf
from arguebuf.load._config import Config, DefaultConfig
from arguebuf.model import Graph


def copy(obj: Graph, config: Config = DefaultConfig) -> Graph:
    """Contents of Graph instance are copied into new Graph object."""

    return load_protobuf(dump_protobuf(obj), obj.name, config)
