import shutil
import typing as t
from pathlib import Path

import deepl_pro as dl
import typer

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
    translator = dl.Translator(
        auth_key, dl.Language(source_lang), dl.Language(target_lang)
    )
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

                target_text = translator.translate_text(source_text)

                with path_pair.target.open("w") as file:
                    file.write(target_text)
