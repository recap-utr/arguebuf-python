from arguebuf.dump import protobuf as dump_protobuf
from arguebuf.load import protobuf as load_protobuf
from arguebuf.load._config import Config
from arguebuf.model import Graph

__all__ = ("copy",)


def copy[T = str](obj: Graph[T], config: Config[T] = Config()) -> Graph[T]:
    """Create a deep copy of a graph by serializing it to protobuf and back."""
    return load_protobuf(dump_protobuf(obj), obj.name, config)
