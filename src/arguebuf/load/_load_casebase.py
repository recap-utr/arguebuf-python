import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Final, Self

from arg_services.cbr.v1beta.model_pb2 import CasebaseFilter as CasebaseFilterProto

from arguebuf.model import Graph
from arguebuf.model.issue import Reporter
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject

from ._load_path import load_file

__all__ = ("CasebaseFilter", "load_casebase")

# folders of other formats (e.g. argdown source files) are skipped
_FORMAT_GLOBS: Final[Mapping[str, str]] = MappingProxyType({
    "aif": "*.json",
    "aml": "*.aml",
    "argdown-json": "*.json",
    "arggraph": "*.xml",
    "arguebuf": "*.json",
    "brat": "*.ann",
    "kialo": "*.txt",
    "microtexts": "*.xml",
    "ova": "*.json",
    "protobuf": "*.json",
    "sadface": "*.json",
    "xaif": "*.json",
})


@dataclass(slots=True, frozen=True)
class FilesystemFilter:
    """Properties of a casebase folder encoded in its path.

    The folder `name/format=aif,lang=en` has the name `name`
    and the properties `format=aif` and `lang=en`.
    """

    name: str
    kwargs: Mapping[str, str]

    @property
    def glob(self) -> str | None:
        """File pattern of the graphs in the folder, None if the format is unknown."""
        return _FORMAT_GLOBS.get(self.kwargs.get("format", ""))

    @classmethod
    def from_path(cls, path: Path) -> Self:
        """Parse the properties of a casebase folder, a key without value is `true`."""
        kwargs: dict[str, str] = {}

        for entry in path.name.replace(" ", "").split(","):
            key, separator, value = entry.partition("=")
            kwargs[key] = value if separator else "true"

        return cls(path.parent.name, kwargs)


@dataclass(slots=True, frozen=True)
class CasebaseFilter:
    """Regular expressions selecting cases from a casebase, they must match completely.

    Attributes:
        name: Pattern for the name of the casebase.
        cases: Pattern for the paths of the cases relative to their casebase folder.
        kwargs: Patterns for the properties of the casebase folder.

    Examples:
        >>> item = CasebaseFilter("micro.*", kwargs={"format": "aif"})
        >>> item.matches_folder(FilesystemFilter("microtexts", {"format": "aif"}), strict=True)
        True
        >>> item.matches_folder(FilesystemFilter("microtexts", {"format": "aifdb"}), strict=True)
        False
    """

    name: str
    cases: str | None = None
    kwargs: Mapping[str, str] = field(default_factory=dict)

    def matches_folder(self, folder: FilesystemFilter, *, strict: bool) -> bool:
        """Check if a casebase folder is selected by this filter.

        If `strict` is set, the folder must not have properties absent in the filter.
        A property of the filter that is absent in the folder never matches.
        """
        return (
            re.fullmatch(self.name, folder.name) is not None
            and (not strict or self.kwargs.keys() == folder.kwargs.keys())
            and all(
                (value := folder.kwargs.get(key)) is not None
                and re.fullmatch(pattern, value) is not None
                for key, pattern in self.kwargs.items()
            )
        )

    def matches_case(self, case: str) -> bool:
        """Check if a case path relative to its casebase folder is selected."""
        return self.cases is None or re.fullmatch(self.cases, case) is not None

    @classmethod
    def from_protobuf(cls, obj: CasebaseFilterProto) -> Self:
        """Generate a filter from its protobuf message, an empty `cases` selects all."""
        return cls(obj.name, obj.cases or None, dict(obj.kwargs))


type CasebaseFilterType = CasebaseFilter | CasebaseFilterProto


def _convert_filters(
    filters: CasebaseFilterType | Iterable[CasebaseFilterType] | None,
) -> list[CasebaseFilter]:
    if filters is None:
        return []

    if isinstance(filters, CasebaseFilter | CasebaseFilterProto):
        filters = [filters]

    return [
        item if isinstance(item, CasebaseFilter) else CasebaseFilter.from_protobuf(item)
        for item in filters
    ]


def load_casebase[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    include: CasebaseFilterType | Iterable[CasebaseFilterType],
    *,
    exclude: CasebaseFilterType | Iterable[CasebaseFilterType] | None = None,
    basepath: Path | str = ".",
    glob: str = "*/*",
    strict_equal: bool = False,
    reconstruct_dialog: bool = False,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> dict[Path, Graph[A, S, E, R, P, N, G]]:
    """Load all cases selected by `include` and not selected by `exclude`.

    Args:
        include: Filters selecting the cases to load.
        exclude: Filters selecting cases to skip, always matched non-strictly.
        basepath: Folder containing the casebases.
        glob: Pattern matching the casebase folders in `basepath`.
        strict_equal: Require the folder properties to equal the filter properties.
        reconstruct_dialog: Reconstruct the dialog of AIF and xAIF graphs
            (see `load_aif`), ignored for other formats.
        codecs: Codecs loading the userdata.

    Returns:
        Dictionary containing all found file paths as well as the loaded graphs.
    """
    include_filters = _convert_filters(include)
    exclude_filters = _convert_filters(exclude)
    graphs: dict[Path, Graph[A, S, E, R, P, N, G]] = {}

    for folder in sorted(Path(basepath).glob(glob)):
        if (
            not folder.is_dir()
            or folder.name.startswith(".")
            or folder.parent.name.startswith(".")
        ):
            continue

        folder_filter = FilesystemFilter.from_path(folder)

        if (glob_pattern := folder_filter.glob) is None:
            continue

        includes = [
            item
            for item in include_filters
            if item.matches_folder(folder_filter, strict=strict_equal)
        ]
        excludes = [
            item
            for item in exclude_filters
            if item.matches_folder(folder_filter, strict=False)
        ]

        if not includes:
            continue

        for file in sorted(folder.glob(f"**/{glob_pattern}")):
            case = file.relative_to(folder).as_posix()

            if (
                any(item.matches_case(case) for item in includes)
                and not any(item.matches_case(case) for item in excludes)
                and file.is_file()
            ):
                graphs[file] = load_file(
                    file, reconstruct_dialog=reconstruct_dialog, codecs=codecs, on_issue=on_issue, strict=strict
                )

    return graphs
