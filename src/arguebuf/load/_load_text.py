from typing import TextIO

from arguebuf.model import Graph

from ._config import Config
from ._load_kialo import load_kialo

__all__ = ("load_text",)


def load_text[T = str](
    obj: TextIO,
    name: str | None = None,
    config: Config[T] = Config(),
) -> Graph[T]:
    """Load a kialo export or a plain text as a graph containing a single atom node."""
    first_line = obj.readline()
    obj.seek(0)

    if "Discussion Title: " in first_line:
        return load_kialo(obj, name, config)

    g = config.graph(name)
    g.add_node(config.AtomNodeClass(config.parse(obj.read())))

    return g
