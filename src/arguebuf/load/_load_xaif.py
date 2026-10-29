from arguebuf.model import Graph
from arguebuf.model.issue import Reporter
from arguebuf.model.resource import Resource
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject
from arguebuf.schemas import xaif

from ._html import parse_html
from ._load_aif import load_aif

__all__ = ("load_xaif",)


def load_xaif[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
](
    obj: xaif.Graph,
    name: str | None = None,
    *,
    reconstruct_dialog: bool = False,
    codecs: Codecs[A, S, E, G, R, P, N] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, G, R, P, N]:
    """Generate Graph structure from xAIF argument graph file.

    The graph in `AIF` is loaded like an AIF graph (see `load_aif`).
    The `text` (a string or `{"txt": ...}`) is HTML whose plain text (see `parse_html`)
    becomes a resource if it is not empty, a missing text yields no resource.
    """
    g = load_aif(obj["AIF"], name, reconstruct_dialog=reconstruct_dialog, codecs=codecs, on_issue=on_issue, strict=strict)
    text = obj.get("text") or ""

    if not isinstance(text, str):
        text = text.get("txt") or ""

    if plain_text := parse_html(text)[0]:
        g.add_resource(
            Resource(plain_text, userdata=codecs.resource.validate_python({}))
        )

    return g
