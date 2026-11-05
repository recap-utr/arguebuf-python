from collections.abc import Mapping
from typing import Any, TypeIs

from arg_services.graph.v1 import graph_pb2
from google.protobuf import proto_json

from arguebuf.model import Graph
from arguebuf.model.issue import Reporter
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject
from arguebuf.schemas import aif, argdown, ova, sadface, xaif

from ._load_aif import load_aif
from ._load_argdown import load_argdown
from ._load_ova import load_ova
from ._load_protobuf import load_protobuf
from ._load_sadface import load_sadface
from ._load_xaif import load_xaif

__all__ = ("load_dict",)

type _Obj = Mapping[str, Any]


def _is_xaif(obj: _Obj) -> TypeIs[xaif.Graph]:
    return "AIF" in obj


def _is_ova(obj: _Obj) -> TypeIs[ova.Graph]:
    return "analysis" in obj


def _is_sadface(obj: _Obj) -> TypeIs[sadface.Graph]:
    return isinstance(metadata := obj.get("metadata"), Mapping) and "core" in metadata


def _is_argdown(obj: _Obj) -> TypeIs[argdown.Graph]:
    return {"statements", "arguments", "relations"} <= obj.keys()


def _is_aif(obj: _Obj) -> TypeIs[aif.Graph]:
    return isinstance(obj.get("nodes"), list)


def load_dict[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    obj: Mapping[str, Any],
    name: str | None = None,
    *,
    reconstruct_dialog: bool = False,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, R, P, N, G]:
    """Generate Graph structure from a dict, detecting its format by its keys.

    The checks are applied in order: `AIF` (xAIF), `analysis` (OVA),
    `metadata.core` (SADFace),
    `statements` with `arguments` and `relations` (Argdown JSON export),
    `nodes` as a list (AIF), and protobuf JSON otherwise.
    `reconstruct_dialog` only applies to AIF and xAIF graphs (see `load_aif`).
    """
    if _is_xaif(obj):
        return load_xaif(
            obj, name, reconstruct_dialog=reconstruct_dialog, codecs=codecs, on_issue=on_issue, strict=strict
        )

    if _is_ova(obj):
        return load_ova(obj, name, codecs=codecs, on_issue=on_issue, strict=strict)

    if _is_sadface(obj):
        return load_sadface(obj, name, codecs=codecs, on_issue=on_issue, strict=strict)

    if _is_argdown(obj):
        return load_argdown(obj, name, codecs=codecs, on_issue=on_issue, strict=strict)

    if _is_aif(obj):
        return load_aif(obj, name, reconstruct_dialog=reconstruct_dialog, codecs=codecs, on_issue=on_issue, strict=strict)

    return load_protobuf(
        proto_json.parse(graph_pb2.Graph, dict(obj)), name, codecs=codecs, on_issue=on_issue, strict=strict
    )
