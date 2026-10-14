import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Self

import typer

InputFolder = Annotated[
    Path,
    typer.Argument(
        help="File or folder to process, folders are searched with INPUT_GLOB.",
        exists=True,
    ),
]
InputGlob = Annotated[
    str,
    typer.Argument(
        help="Glob pattern selecting the files within INPUT_FOLDER, e.g., '**/*.json'."
    ),
]
OutputFolder = Annotated[
    Path | None,
    typer.Option(
        help="File or folder to write the results to, defaults to INPUT_FOLDER.",
        show_default=False,
    ),
]
Clean = Annotated[
    bool, typer.Option(help="Delete the output folder before processing.")
]
Overwrite = Annotated[
    bool, typer.Option(help="Overwrite existing output files instead of skipping.")
]
Start = Annotated[
    int,
    typer.Option(
        help="Position of the first input file to process, used to resume a run.",
        min=1,
    ),
]
SourceLang = Annotated[
    str, typer.Argument(help="DeepL code of the source language, e.g., 'DE'.")
]
TargetLang = Annotated[
    str, typer.Argument(help="DeepL code of the target language, e.g., 'EN-US'.")
]
AuthKey = Annotated[
    str,
    typer.Option(
        help="DeepL API authentication key, prefer the environment variable.",
        envvar="DEEPL_AUTH_KEY",
        show_default=False,
    ),
]


@dataclass(slots=True, frozen=True)
class PathPair:
    """A pair of paths for modification of files."""

    source: Path
    target: Path

    @classmethod
    def create(
        cls,
        path_in: Path,
        path_out: Path,
        input_glob: str | None,
        output_suffix: str | None,
    ) -> list[Self]:
        pairs: list[Self] = []

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
                cls(file_in, file_out)
                for file_in, file_out in zip(files_in, files_out, strict=True)
            )

        else:
            raise ValueError(
                "Folder given as input. Please also provide a folder as output together"
                " with a shell globbing pattern and an output suffix."
            )

        return pairs


def _label(path_pair: PathPair | None) -> str:
    return path_pair.source.name if path_pair else ""


def pending_pairs(
    input_folder: Path,
    output_folder: Path | None,
    input_glob: str | None,
    output_suffix: str | None,
    clean: bool,
    overwrite: bool,
    start: int,
) -> Iterator[PathPair]:
    """Yield the path pairs still to be processed while showing a progress bar.

    The output folder defaults to the input folder.
    """
    output_folder = output_folder or input_folder

    if clean:
        # cleaning an output folder that contains the inputs would delete them
        if input_folder.resolve().is_relative_to(output_folder.resolve()):
            raise typer.BadParameter(
                "The output folder must not contain the input when using --clean."
            )

        shutil.rmtree(output_folder, ignore_errors=True)
        output_folder.mkdir(parents=True)

    pairs = PathPair.create(input_folder, output_folder, input_glob, output_suffix)

    with typer.progressbar(
        pairs[start - 1 :], item_show_func=_label, show_pos=True
    ) as bar:
        for path_pair in bar:
            if overwrite or not path_pair.target.exists():
                yield path_pair
