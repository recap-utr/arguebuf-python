from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, Literal, TextIO

from arguebuf.model import Graph
from arguebuf.model.issue import Reporter
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject

from ._load_aml import load_aml
from ._load_brat import load_brat
from ._load_json import load_json
from ._load_microtexts import load_microtexts
from ._load_text import load_text

__all__ = ("SUFFIXES", "FileFormat", "load_io")

type FileFormat = Literal["json", "brat", "text", "aml", "microtexts"]
"""Formats of files, see `SUFFIXES`."""

SUFFIXES: Final[Mapping[FileFormat, tuple[str, ...]]] = MappingProxyType(
    {
        "json": (".json",),
        "brat": (".ann",),
        "text": (".txt",),
        "aml": (".aml",),
        "microtexts": (".xml",),
    }
)
"""Lowercase file suffixes by format."""


def load_io[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    obj: TextIO,
    suffix: str,
    *,
    name: str | None = None,
    reconstruct_dialog: bool = False,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, R, P, N, G]:
    """Generate Graph structure from a file object based on the file `suffix` (case-insensitive).

    `reconstruct_dialog` only applies to AIF and xAIF graphs (see `load_aif`).

    Raises:
        ValueError: If the suffix is not in `SUFFIXES`.
    """
    match next(
        (format for format, items in SUFFIXES.items() if suffix.lower() in items), None
    ):
        case "brat":
            return load_brat(
                obj, name=name, codecs=codecs, on_issue=on_issue, strict=strict
            )
        case "text":
            return load_text(
                obj, name=name, codecs=codecs, on_issue=on_issue, strict=strict
            )
        case "aml":
            return load_aml(
                obj, name=name, codecs=codecs, on_issue=on_issue, strict=strict
            )
        case "microtexts":
            return load_microtexts(
                obj, name=name, codecs=codecs, on_issue=on_issue, strict=strict
            )
        case "json":
            return load_json(
                obj,
                name=name,
                reconstruct_dialog=reconstruct_dialog,
                codecs=codecs,
                on_issue=on_issue,
                strict=strict,
            )
        case _:
            raise ValueError(f"The suffix '{suffix}' is not supported.")
