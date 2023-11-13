import re
import typing as t
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from arg_services.cbr.v1beta.model_pb2 import CasebaseFilter as CasebaseFilterProto

from arguebuf.model import Graph

from ._config import Config, DefaultConfig
from ._load_path import load_file, load_folder

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
    None: "*",
}

DEFAULT_GLOB = "*"


@dataclass
class FilesystemFilter:
    name: str
    kwargs: dict[str, str]

    def __init__(self, name: str, **kwargs: str) -> None:
        self.name = name
        self.kwargs = kwargs

    @property
    def glob(self) -> str:
        return format2glob.get(self.kwargs.get("format"), DEFAULT_GLOB)

    @classmethod
    def from_path(cls, path: Path) -> "FilesystemFilter":
        kwargs: dict[str, str] = {}
        entries = path.name.replace(" ", "").split(",")

        for entry in entries:
            key, *values = entry.split("=")
            value = values[0] if len(values) == 1 else "true"
            kwargs[key] = value

        return cls(path.parent.name, **kwargs)


class CasebaseFilter:
    name: re.Pattern
    cases: t.Optional[re.Pattern]
    kwargs: dict[str, re.Pattern]

    def __init__(self, name: str, cases: t.Optional[str] = None, **kwargs: str):
        self.name = re.compile(name)
        self.cases = re.compile(cases) if cases is not None else None
        self.kwargs = {}

        for key, value in kwargs.items():
            self.kwargs[key] = re.compile(value)

    def __eq__(self, other: FilesystemFilter) -> bool:
        return self.kwargs == other.kwargs and self >= other

    def __ge__(self, other: FilesystemFilter) -> bool:
        return all(
            pattern.match(other.kwargs.get(kwarg, "null"))
            for kwarg, pattern in self.kwargs.items()
        )

    @classmethod
    def from_protobuf(cls, filter: CasebaseFilterProto) -> "CasebaseFilter":
        return cls(filter.name, filter.cases, **filter.kwargs)


CasebaseFilterType = t.Union[CasebaseFilter, CasebaseFilterProto]


def convert_filters(
    filters: t.Union[CasebaseFilterType, t.Iterable[CasebaseFilterType], None]
) -> list[CasebaseFilter]:
    if filters is None:
        return []

    if not isinstance(filters, Iterable):
        filters = [filters]

    return [
        (
            filter
            if isinstance(filter, CasebaseFilter)
            else CasebaseFilter.from_protobuf(filter)
        )
        for filter in filters
    ]


def load_casebase(
    include: t.Union[CasebaseFilterType, t.Iterable[CasebaseFilterType]],
    exclude: t.Union[CasebaseFilterType, t.Iterable[CasebaseFilterType], None] = None,
    basepath: t.Union[Path, str] = ".",
    glob: str = "*/*",
    config: Config = DefaultConfig,
    strict_equal: bool = False,
):
    graphs: dict[Path, Graph] = {}

    if not isinstance(basepath, Path):
        basepath = Path(basepath)

    include = convert_filters(include)
    exclude = convert_filters(exclude)

    # TODO: exclude currently not applied

    for filter in include:
        for path in sorted(basepath.glob(glob)):
            if (
                path.is_dir()
                and filter.name.match(path.parent.name)
                and not path.parent.name.startswith(".")
                and not path.name.startswith(".")
            ):
                graphs |= _from_casebase_single(filter, path, config, strict_equal)

    return graphs


def _from_casebase_single(
    user_filter: CasebaseFilter,
    path: Path,
    config: Config,
    strict_equal: bool,
):
    filesystem_filter = FilesystemFilter.from_path(path)

    if (strict_equal and user_filter == filesystem_filter) or (
        not strict_equal and user_filter >= filesystem_filter
    ):
        glob = f"**/{filesystem_filter.glob}"

        if user_filter.cases is not None:
            return {
                file: load_file(file, config=config)
                for file in sorted(path.glob(glob))
                if file.is_file()
                and user_filter.cases.match(str(file.relative_to(path)))
            }

        return load_folder(path, glob, config=config)

    return {}
