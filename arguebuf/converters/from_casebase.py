from __future__ import annotations

import re
import typing as t
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from arguebuf.converters.config import ConverterConfig, DefaultConverter
from arguebuf.converters.from_path import from_file, from_folder
from arguebuf.models.graph import Graph

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
    kwargs: t.Dict[str, str]

    def __init__(self, name: str, **kwargs: str) -> None:
        self.name = name
        self.kwargs = kwargs

    @property
    def glob(self) -> str:
        return format2glob.get(self.kwargs.get("format"), DEFAULT_GLOB)

    @classmethod
    def from_path(cls, path: Path) -> FilesystemFilter:
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
    kwargs: t.Dict[str, re.Pattern]

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


def from_casebase(
    basepath: t.Union[Path, str],
    include: t.Union[CasebaseFilter, t.Iterable[CasebaseFilter]],
    exclude: t.Union[CasebaseFilter, t.Iterable[CasebaseFilter], None] = None,
    glob: str = "*/*",
    config: ConverterConfig = DefaultConverter,
    strict_equal: bool = False,
):
    graphs: dict[Path, Graph] = {}

    if not isinstance(basepath, Path):
        basepath = Path(basepath)

    if not isinstance(include, Iterable):
        include = [include]

    # if isinstance(exclude, CasebaseFilter):
    #     exclude = [exclude]

    for filter in include:
        for path in sorted(basepath.glob(glob)):
            if (
                path.is_dir()
                and filter.name.match(path.parent.name)
                and not path.parent.name.startswith(".")
                and not path.name.startswith(".")
            ):
                graphs.update(_from_casebase_single(filter, path, config, strict_equal))

    return graphs


def _from_casebase_single(
    user_filter: CasebaseFilter,
    path: Path,
    config: ConverterConfig,
    strict_equal: bool,
):
    filesystem_filter = FilesystemFilter.from_path(path)

    if (strict_equal and user_filter == filesystem_filter) or (
        not strict_equal and user_filter >= filesystem_filter
    ):
        glob = f"**/{filesystem_filter.glob}"

        if user_filter.cases is not None:
            graphs = {}

            for file in sorted(path.glob(glob)):
                if file.is_file() and user_filter.cases.match(
                    str(file.relative_to(path))
                ):
                    graphs[file] = from_file(file, config=config)

            return graphs

        return from_folder(path, glob, config=config)

    return {}
