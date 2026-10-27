from pathlib import Path

import pytest

import arguebuf as ag


@pytest.mark.parametrize("single_file", (True, False))
def test_convert_text_folder(tmp_path: Path, single_file: bool) -> None:
    pytest.importorskip("typer")
    pytest.importorskip("deepl")

    from arguebuf.cli.graph import convert

    inputs = tmp_path / "inputs"
    annotation = inputs / "nested" / "graph.ann"
    annotation.parent.mkdir(parents=True)
    annotation.write_text("T1\tClaim 0 5\tClaim\n", encoding="utf-8")
    texts = tmp_path / "texts"
    text = texts / ("graph.source" if single_file else "nested/graph.source")
    text.parent.mkdir(parents=True)
    text.write_text("Source text", encoding="utf-8")
    output = tmp_path / ("output.json" if single_file else "output")

    convert(
        annotation if single_file else inputs,
        "**/*.ann",
        output_folder=output,
        text_folder=texts,
        text_suffix=".source",
    )
    loaded = ag.load.file(output if single_file else output / "nested/graph.json")

    assert [resource.text for resource in loaded.resources.values()] == ["Source text"]
