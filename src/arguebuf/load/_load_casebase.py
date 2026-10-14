import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from arg_services.cbr.v1beta.model_pb2 import CasebaseFilter as CasebaseFilterProto

from arguebuf.model import Graph

from ._config import Config, DefaultConfig
from ._load_path import load_file

__all__ = ("CasebaseFilter", "load_casebase")

format2glob = {
    "aif": "*.json",
    "aml": "*.aml",
    "argdown": "*.json",
    "arggraph": "*.xml",
    "arguebuf": "*.json",
    "brat": "*.ann",
    "kialo": "*.txt",
    "microtexts": "*.xml",
    "ova": "*.json",
    "protobuf": "*.json",
}

DEFAULT_GLOB = "*"


@dataclass(slots=True, frozen=True)
class FilesystemFilter:
    """Properties of a casebase folder encoded in its path.

    The folder `name/format=aif,lang=en` has the name `name`
    and the properties `format=aif` and `lang=en`.
    """

    name: str
    kwargs: Mapping[str, str]

    @property
    def glob(self) -> str:
        return format2glob.get(self.kwargs.get("format", ""), DEFAULT_GLOB)

    @classmethod
    def from_path(cls, path: Path) -> Self:
        kwargs: dict[str, str] = {}

        for entry in path.name.replace(" ", "").split(","):
            key, *values = entry.split("=")
            kwargs[key] = values[0] if len(values) == 1 else "true"

        return cls(path.parent.name, kwargs)


class CasebaseFilter:
    """Regular expressions selecting cases from a casebase.

    Args:
        name: Pattern for the name of the casebase.
        cases: Pattern for the paths of the cases relative to their casebase folder.
        kwargs: Patterns for the properties of the casebase folder.
    """

    __slots__ = ("cases", "kwargs", "name")

    name: re.Pattern[str]
    cases: re.Pattern[str] | None
    kwargs: dict[str, re.Pattern[str]]

    def __init__(self, name: str, cases: str | None = None, **kwargs: str) -> None:
        self.name = re.compile(name)
        self.cases = re.compile(cases) if cases else None
        self.kwargs = {key: re.compile(value) for key, value in kwargs.items()}

    def matches_folder(self, folder: FilesystemFilter, strict: bool) -> bool:
        """Check if a casebase folder is selected by this filter.

        If `strict` is set, the folder must not have properties absent in the filter.
        """
        return (
            self.name.match(folder.name) is not None
            and (not strict or self.kwargs.keys() == folder.kwargs.keys())
            and all(
                pattern.match(folder.kwargs.get(key, "null"))
                for key, pattern in self.kwargs.items()
            )
        )

    def matches_case(self, case: str) -> bool:
        """Check if a case path relative to its casebase folder is selected."""
        return self.cases is None or self.cases.match(case) is not None

    @classmethod
    def from_protobuf(cls, obj: CasebaseFilterProto) -> Self:
        return cls(obj.name, obj.cases, **obj.kwargs)


CasebaseFilterType = CasebaseFilter | CasebaseFilterProto


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


def load_casebase(
    include: CasebaseFilterType | Iterable[CasebaseFilterType],
    exclude: CasebaseFilterType | Iterable[CasebaseFilterType] | None = None,
    basepath: Path | str = ".",
    glob: str = "*/*",
    config: Config = DefaultConfig,
    strict_equal: bool = False,
) -> dict[Path, Graph]:
    """Load all cases selected by `include` and not selected by `exclude`.

    Args:
        include: Filters selecting the cases to load.
        exclude: Filters selecting cases to skip, always matched non-strictly.
        basepath: Folder containing the casebases.
        glob: Pattern matching the casebase folders in `basepath`.
        config: Options for loading the graphs.
        strict_equal: Require the folder properties to equal the filter properties.

    Returns:
        Dictionary containing all found file paths as well as the loaded graphs.
    """
    include_filters = _convert_filters(include)
    exclude_filters = _convert_filters(exclude)
    graphs: dict[Path, Graph] = {}

    for folder in sorted(Path(basepath).glob(glob)):
        if (
            not folder.is_dir()
            or folder.name.startswith(".")
            or folder.parent.name.startswith(".")
        ):
            continue

        folder_filter = FilesystemFilter.from_path(folder)
        includes = [
            item
            for item in include_filters
            if item.matches_folder(folder_filter, strict_equal)
        ]
        excludes = [
            item
            for item in exclude_filters
            if item.matches_folder(folder_filter, False)
        ]

        if not includes:
            continue

        for file in sorted(folder.glob(f"**/{folder_filter.glob}")):
            case = str(file.relative_to(folder))

            if (
                any(item.matches_case(case) for item in includes)
                and not any(item.matches_case(case) for item in excludes)
                and file.is_file()
            ):
                graphs[file] = load_file(file, config=config)

    return graphs
