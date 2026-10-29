from io import StringIO
from typing import TextIO

from arguebuf.model import Graph
from arguebuf.model.issue import Reporter
from arguebuf.model.node import AtomNode
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject

from ._load_kialo import load_kialo, title_pattern

__all__ = ("load_text",)


def load_text[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
](
    obj: TextIO,
    name: str | None = None,
    *,
    codecs: Codecs[A, S, E, G, R, P, N] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, G, R, P, N]:
    """Load a kialo export or a plain text as a graph containing a single atom node."""
    text = obj.read()

    if title_pattern.search(text.partition("\n")[0]):
        return load_kialo(StringIO(text), name, codecs=codecs, on_issue=on_issue, strict=strict)

    g: Graph[A, S, E, G, R, P, N] = Graph(
        name, userdata=codecs.graph.validate_python({})
    )
    g.add_node(AtomNode(text, userdata=codecs.atom.validate_python({})))

    return g
