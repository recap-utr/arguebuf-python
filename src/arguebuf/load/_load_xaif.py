from arguebuf.model import Graph
from arguebuf.schemas import xaif

from ._config import Config
from ._load_aif import load_aif

__all__ = ("load_xaif",)


def load_xaif[T = str](
    obj: xaif.Graph, name: str | None = None, config: Config[T] = Config()
) -> Graph[T]:
    """Generate Graph structure from xAIF argument graph file."""
    return load_aif(obj["AIF"], name, config)
