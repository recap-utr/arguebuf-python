from __future__ import annotations

import typing as t
from dataclasses import asdict, dataclass, fields
from pathlib import Path

from arguebuf.converters.from_path import from_folder
from arguebuf.models.graph import Graph

format2pattern = {
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

DEFAULT_PATTERN = "*"


@dataclass
class CasebaseFilter:
    name: str
    lang: t.Optional[str] = None
    format: t.Optional[str] = None
    variant: t.Optional[str] = None
    schemes: t.Optional[bool] = None

    @property
    def pattern(self) -> str:
        if self.format is not None:
            return format2pattern.get(self.format, DEFAULT_PATTERN)

        return DEFAULT_PATTERN

    @classmethod
    def from_path(cls, path: Path) -> CasebaseFilter:
        filter = CasebaseFilter(path.parent.name)
        entries = path.name.replace(" ", "").split(",")

        for entry in entries:
            key, *values = entry.split("=")
            value = values[0] if len(values) == 1 else True

            setattr(filter, key, value)

        return filter

    def to_path(self) -> Path:
        attributes = {
            key: value
            for key, value in asdict(self)
            if value is not None and key != "name"
        }
        folder_name = ",".join(
            f"{key}={value}"
            for key, value in sorted(attributes.items(), key=lambda x: x[0])
        )

        return Path(self.name, folder_name)

    def __eq__(self, other: CasebaseFilter) -> bool:
        return all(
            getattr(self, field.name) is None
            or getattr(other, field.name) is None
            or (getattr(self, field.name) == getattr(other, field.name))
            for field in fields(CasebaseFilter)
        )

    def __ge__(self, other: CasebaseFilter) -> bool:
        return all(
            getattr(self, field.name) is None
            or (getattr(self, field.name) == getattr(other, field.name))
            for field in fields(CasebaseFilter)
        )

    def __le__(self, other: CasebaseFilter) -> bool:
        return all(
            getattr(other, field.name) is None
            or (getattr(self, field.name) == getattr(other, field.name))
            for field in fields(CasebaseFilter)
        )


def from_casebase(
    filters: t.Iterable[CasebaseFilter],
    basepath: Path = Path.cwd(),
    strict_equal: bool = False,
):
    graphs: dict[Path, Graph] = {}

    for input_filter in filters:
        searchpath = basepath / input_filter.name

        for folder in searchpath.iterdir():
            if folder.is_dir():
                candidate_filter = CasebaseFilter.from_path(folder)

                if (strict_equal and input_filter == candidate_filter) or (
                    not strict_equal and input_filter >= candidate_filter
                ):
                    graphs.update(from_folder(folder, f"**/{candidate_filter.pattern}"))

    return graphs
