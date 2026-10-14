from pathlib import Path

import typer
from deepl import DeepLClient

from . import model
from .translator import Translator

cli = typer.Typer()


@cli.command()
def translate(
    input_folder: Path,
    source_lang: str,
    target_lang: str,
    auth_key: str,
    input_glob: str,
    output_suffix: str,
    output_folder: Path | None = None,
    clean: bool = False,
    overwrite: bool = False,
    start: int = 1,
) -> None:
    translator = Translator(DeepLClient(auth_key), source_lang, target_lang)

    for path_pair in model.pending_pairs(
        input_folder, output_folder, input_glob, output_suffix, clean, overwrite, start
    ):
        path_pair.target.write_text(
            translator.translate_text(path_pair.source.read_text())
        )
