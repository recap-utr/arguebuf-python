import json
from pathlib import Path

import pytest

import arguebuf as ag

SAMPLES = Path("data", "arguebase", "argdown-examples", "format=argdown-json,lang=en")


@pytest.mark.parametrize("path", sorted(SAMPLES.glob("*.json")), ids=lambda p: p.stem)
def test_argdown_samples(path: Path) -> None:
    graph = ag.load.argdown(json.loads(path.read_text()))

    assert graph.nodes

    for edge in graph.edges.values():
        assert graph.nodes[edge.source.id] is edge.source
        assert graph.nodes[edge.target.id] is edge.target
