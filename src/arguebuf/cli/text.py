from typing import Annotated

import typer
from deepl import DeepLClient

from . import model
from .translator import Translator

cli = typer.Typer(no_args_is_help=True)


@cli.command()
def translate(
    input_folder: model.InputFolder,
    source_lang: model.SourceLang,
    target_lang: model.TargetLang,
    auth_key: model.AuthKey,
    input_glob: model.InputGlob,
    output_suffix: Annotated[
        str, typer.Argument(help="Suffix of the translated files, e.g., '.txt'.")
    ],
    output_folder: model.OutputFolder = None,
    clean: model.Clean = False,
    overwrite: model.Overwrite = False,
    start: model.Start = 1,
) -> None:
    """Translate plain text files with DeepL."""
    translator = Translator(DeepLClient(auth_key), source_lang, target_lang)

    for path_pair in model.pending_pairs(
        input_folder, output_folder, input_glob, output_suffix, clean, overwrite, start
    ):
        path_pair.target.write_text(
            translator.translate_text(path_pair.source.read_text())
        )
