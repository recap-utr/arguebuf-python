import html
import re
import shutil
from pathlib import Path

import pytest

import arguebuf as ag


@pytest.fixture
def graph() -> ag.Graph:
    g = ag.GraphDraft("Test")
    atom = ag.AtomNode("Claim")
    scheme = ag.SchemeNode(ag.Support.DEFAULT)
    g.add_node(atom)
    g.add_node(scheme)
    g.add_edge(ag.Edge(atom.id, scheme.id))

    return g.freeze()


def test_render_graphviz(graph: ag.Graph, tmp_path: Path):
    gv = ag.dump.graphviz(graph)
    assert gv is not None

    ag.render.graphviz(gv, tmp_path / "graph.png")
    assert (tmp_path / "graph.png").stat().st_size > 0


def test_graphviz_escaping():
    g = ag.GraphDraft()
    atom = ag.AtomNode('x ab-cd\\ "b" \\N')
    g.add_node(atom)
    g.major_claim = atom
    gv = ag.dump.graphviz(g.freeze(), wrap_col=6)

    assert gv is not None
    assert "root=true" in gv.string()

    # the label is rendered literally and wrapped only at whitespace
    svg = gv.draw(format="svg", prog="dot")

    assert svg is not None
    assert [
        html.unescape(text)
        for text in re.findall(r"<text[^>]*>(.*?)</text>", svg.decode())
    ] == ["x", "ab-cd\\", '"b" \\N']


@pytest.mark.skipif(shutil.which("d2") is None, reason="requires the d2 executable")
def test_render_d2(graph: ag.Graph, tmp_path: Path):
    d2 = ag.dump.d2(graph)
    assert d2 is not None

    ag.render.d2(d2, tmp_path / "graph.png")
    assert (tmp_path / "graph.png").stat().st_size > 0
