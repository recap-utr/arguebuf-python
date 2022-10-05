import shutil
import typing as t
from pathlib import Path

import deepl
import typer
from arguebuf.cli.translator import Translator

from . import model

cli = typer.Typer()


@cli.command()
def translate(
    input_folder: Path,
    source_lang: str,
    target_lang: str,
    auth_key: str,
    input_glob: str,
    output_suffix: str,
    output_folder: t.Optional[Path] = None,
    clean: bool = False,
    overwrite: bool = False,
    start: int = 1,
) -> None:
    if not output_folder:
        output_folder = input_folder

    if clean:
        shutil.rmtree(output_folder)
        output_folder.mkdir()

    paths = model.PathPair.create(
        input_folder, output_folder, input_glob, output_suffix
    )
    translator = Translator(auth_key, source_lang, target_lang)
    bar: t.Iterable[model.PathPair]

    with typer.progressbar(
        paths[start - 1 :],
        item_show_func=model.PathPair.label,
        show_pos=True,
    ) as bar:
        for path_pair in bar:
            if overwrite or not path_pair.target.exists():
                with path_pair.source.open("r") as file:
                    source_text = file.read()

                translation = translator.translate(source_text)

                with path_pair.target.open("w") as file:
                    file.write(translation)
