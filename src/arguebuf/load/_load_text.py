from io import StringIO
from typing import TextIO

from arguebuf.model import Graph, GraphDraft
from arguebuf.model.issue import Reporter
from arguebuf.model.node import AtomNode
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject

from ._load_kialo import TITLE_PATTERN, load_kialo

__all__ = ("load_text",)


def load_text[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    obj: TextIO,
    *,
    name: str | None = None,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, R, P, N, G]:
    """Load a kialo export or a plain text as a graph containing a single atom node."""
    text = obj.read()

    if TITLE_PATTERN.search(text.partition("\n")[0]):
        return load_kialo(
            StringIO(text), name=name, codecs=codecs, on_issue=on_issue, strict=strict
        )

    g: GraphDraft[A, S, E, R, P, N, G] = GraphDraft(
        name, userdata=codecs.graph.validate_python({})
    )
    g.add_node(AtomNode(text, userdata=codecs.atom.validate_python({})))

    return g.freeze()
