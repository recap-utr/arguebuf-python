from collections.abc import Mapping

from pydantic import TypeAdapter

from arguebuf.model import Graph
from arguebuf.model.issue import Reporter
from arguebuf.model.resource import Resource
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject
from arguebuf.schemas import xaif

from ._helpers import Context, validate
from ._html import parse_html
from ._load_aif import build_aif

__all__ = ("load_xaif",)

_SCHEMA = TypeAdapter(xaif.Graph)


def load_xaif[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    obj: Mapping[str, object],
    *,
    name: str | None = None,
    reconstruct_dialog: bool = False,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, R, P, N, G]:
    """Generate Graph structure from xAIF argument graph file.

    The graph in `AIF` is loaded like an AIF graph (see `load_aif`).
    The `text` (a string or `{"txt": ...}`) is HTML whose plain text (see `parse_html`)
    becomes a resource if it is not empty, a missing text yields no resource.
    The input is validated first, raising a `GraphError` of code `invalid-input`.
    """
    xaif_obj = validate("xAIF", _SCHEMA, obj)
    g = build_aif(
        xaif_obj["AIF"], name, reconstruct_dialog, Context(codecs, on_issue, strict)
    )
    text = xaif_obj.get("text")

    if isinstance(text, Mapping):
        text = text.get("txt")

    if not (plain_text := parse_html(text or "")[0]):
        return g

    return g.edit(
        lambda draft: draft.add_resource(
            Resource(plain_text, userdata=codecs.resource.validate_python({}))
        )
    )
