import re
import typing as t

from arguebuf.model import Graph, utils
from arguebuf.model.node import AtomNode, Attack, Rephrase, Support

from ._config import Config, DefaultConfig
from ._load_kialo import load_kialo

__all__ = ("load_text",)


def load_text(
    obj: t.TextIO,
    name: t.Optional[str] = None,
    config: Config = DefaultConfig,
) -> Graph:
    if "Discussion Title: " in obj.readline():
        obj.seek(0)
        return load_kialo(obj, name, config)

    text = obj.read()

    g = config.GraphClass(name)
    g.add_node(AtomNode(utils.parse(text, config.nlp)))

    return g
