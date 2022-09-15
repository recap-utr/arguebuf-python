from __future__ import annotations

import typing as t
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PathPair:
    """A pair of paths for modification of files."""

    source: Path
    target: Path

    @classmethod
    def create(
        cls,
        path_in: Path,
        path_out: Path,
        input_glob: t.Optional[str],
        output_suffix: t.Optional[str],
    ) -> t.List[PathPair]:
        pairs: list[PathPair] = []

        if path_in.is_file():
            if path_out.suffix:
                pairs.append(cls(path_in, path_out))
            elif output_suffix:
                pairs.append(cls(path_in, path_out.with_suffix(output_suffix)))
            else:
                raise ValueError(
                    "File given as input. Please also provide a file as output."
                )

        elif path_in.is_dir() and input_glob and output_suffix:
            path_out.mkdir(parents=True, exist_ok=True)

            files_in = sorted(path_in.glob(input_glob))
            files_out: list[Path] = []

            for file_in in files_in:
                file_out = path_out / file_in.relative_to(path_in)
                file_out = file_out.with_suffix(output_suffix)
                file_out.parent.mkdir(parents=True, exist_ok=True)

                files_out.append(file_out)

            pairs.extend(
                cls(file_in, file_out) for file_in, file_out in zip(files_in, files_out)
            )

        else:
            raise ValueError(
                "Folder given as input. Please also provide a folder as output together with a shell globbing pattern and an output suffix."
            )

        return pairs

    @staticmethod
    def label(path_pair: t.Optional[PathPair]) -> str:
        """Generate a string for representing a path pair.

        Args:
            path_pair: The item that should be represented.

        Returns:
            A label for use in UI contexts.
        """

        return path_pair.source.name if path_pair else ""
