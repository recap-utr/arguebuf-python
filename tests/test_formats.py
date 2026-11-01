"""Regression tests for the format loaders and dumpers."""

import io
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import override

import pytest
from arg_services.graph.v1 import graph_pb2

import arguebuf as ag
from arguebuf.load._helpers import stringify_id
from arguebuf.load._html import Span, parse_html
from arguebuf.schemas import aif, ova

KIALO = """Discussion Title: Title

1. Claim
1.1. Pro: -> See 1.2.
1.2. Con: Second
continued\x20\x20

1.2.1. Pro: -> See 1.1.
1.2.1.1. Con: Child of a reference
1.3. Pro: [Link](https://x.org/a_(b)) \\(c\\)
"""


def _edges(g: ag.Graph) -> set[tuple[str, str]]:
    return {(edge.source, edge.target) for edge in g.edges.values()}


def test_kialo():
    g = ag.load.kialo(io.StringIO(KIALO))

    assert g.name == "Title"
    assert g.major_claim == "1."
    assert g.atom_nodes.keys() == {"1.", "1.2.", "1.2.1.1.", "1.3."}
    assert g.atom_nodes["1.2."].text == "Second\ncontinued"
    assert g.atom_nodes["1.3."].text == "Link (c)"
    # forward reference and the children of a reference
    assert ("1.2.", "1.1.scheme") in _edges(g)
    assert ("1.2.1.scheme", "1.2.") in _edges(g)
    assert ("1.2.1.1.scheme", "1.2.") in _edges(g)

    with pytest.raises(ValueError, match="not unique"):
        ag.load.kialo(io.StringIO(KIALO + "1.2. Pro: Duplicate\n"))


def test_text_without_seek():
    class Stream(io.StringIO):
        @override
        def seek(self, pos: int, whence: int = 0, /) -> int:
            raise io.UnsupportedOperation

    assert len(ag.load.io(Stream(KIALO), ".txt").atom_nodes) == 4

    with pytest.raises(ValueError, match="not supported"):
        ag.load.io(io.StringIO(KIALO), ".md")


def test_brat(caplog: pytest.LogCaptureFixture):
    ann = (
        'T1\tMajorClaim 0 1\t"first"\n'
        "\n"
        "T2\tMajorClaim 2 3\tsecond\n"
        "T3\tPremise 4 5\tpremise\n"
        "A1\tStance T3 Against\n"
        "R1\tsupports Arg1:T3 Arg2:T2\t\n"
        "R2\tattacks Arg2:T1 Arg1:T3\n"
        "garbage\n"
        "A2\tStance T3 Neutral\n"
        "R3\tcontradicts Arg1:T3 Arg2:T2\n"
    )

    # the suffix is matched case-insensitively
    with caplog.at_level(logging.WARNING):
        g = ag.load.io(io.StringIO(ann), ".ANN")

    assert g.major_claim and g.atom_nodes[g.major_claim].text == '"first"'
    assert {node.id: node.label for node in g.scheme_nodes.values()} == {
        "T2scheme": "Rephrase",
        "A1": "Attack",
        "R1": "Support",
        "R2": "Attack",
    }
    assert ("T2scheme", "T1") in _edges(g)
    assert ("A1", "T1") in _edges(g)
    assert ("R1", "T2") in _edges(g)
    assert {("T3", "R2"), ("R2", "T1")} <= _edges(g)
    assert len(caplog.records) == 2


def test_microtexts():
    xml = """<arggraph id="m">
        <edu id="e1">Claim</edu>
        <edu id="e2">Premise one</edu>
        <edu id="e3">and two</edu>
        <joint id="j1" />
        <edu id="e4">Undercutter</edu>
        <edu id="e5">Addition</edu>
        <joint id="j1" />
        <adu id="a1" type="pro" />
        <adu id="a2" type="pro" />
        <adu id="a3" type="opp" />
        <adu id="a4" type="pro" />
        <edge id="c1" src="e1" trg="a1" type="seg" />
        <edge id="c2" src="e2" trg="j1" type="seg" />
        <edge id="c3" src="e3" trg="j1" type="seg" />
        <edge id="c4" src="j1" trg="a2" type="seg" />
        <edge id="c6" src="e4" trg="a3" type="seg" />
        <edge id="c7" src="e5" trg="a4" type="seg" />
        <edge id="c8" src="a3" trg="c5" type="und" />
        <edge id="c5" src="a2" trg="a1" type="sup" />
        <edge id="c9" src="a4" trg="c5" type="add" />
    </arggraph>"""
    g = ag.load.microtexts(io.StringIO(xml))

    assert g.major_claim == "a1"
    assert g.atom_nodes["a2"].text == "Premise one and two"
    # the undercutter precedes its target edge
    assert {("a3", "c8"), ("c8", "c5"), ("a4", "c5")} <= _edges(g)
    assert g.edges["c9"].source == "a4"


def test_aml():
    xml = """<ARG><AU>
        <PROP identifier="A"><PROPTEXT>Claim</PROPTEXT></PROP>
        <LA>
            <AU><PROP identifier="B"><PROPTEXT>Premise one</PROPTEXT>
                <INSCHEME scheme="Argument from Sign" schid="0" /></PROP></AU>
            <AU><PROP identifier="C"><PROPTEXT>Premise two</PROPTEXT></PROP></AU>
        </LA>
    </AU></ARG>"""
    g = ag.load.aml(io.StringIO(xml))

    assert g.major_claim == "A"
    assert [node.label for node in g.scheme_nodes.values()] == ["Support: Sign"]
    assert _edges(g) == {("B", "Bscheme"), ("C", "Bscheme"), ("Bscheme", "A")}


def test_sadface():
    edited = "2020-01-02T03:04:05"
    obj = {
        "metadata": {"core": {"id": "g", "version": "0.5", "edited": edited}},
        "resources": [{"id": "r", "content": "Text A", "type": "text"}],
        "nodes": [
            {
                "id": "a",
                "type": "atom",
                "text": "A",
                "sources": [{"resource_id": "r", "text": "A", "offset": 5}],
            },
            {"id": "b", "type": "atom", "text": "B"},
            {"id": "i", "type": "inference", "name": "Expert Opinion"},
            {"id": "c", "type": "conflict", "name": "disagree"},
            {"id": "s", "type": "scheme", "name": "conflict"},
        ],
        "edges": [{"id": "e", "source_id": "a", "target_id": "i"}],
    }
    g = ag.load.dict(obj)

    assert {node.id: node.label for node in g.scheme_nodes.values()} == {
        "i": "Support: Expert Opinion",
        "c": "Attack",
        "s": "Attack",
    }
    assert g.atom_nodes["a"].reference == ag.Reference(
        "A", resource="r", offset=5
    )
    assert g.userdata == {"sadfaceVersion": "0.5"}
    assert not g.analysts
    assert _edges(g) == {("a", "i")}
    assert g.edges["e"].userdata == {}
    assert (
        g.metadata.created
        == g.metadata.updated
        == datetime(2020, 1, 2, 3, 4, 5, tzinfo=UTC)
    )


def test_ova(caplog: pytest.LogCaptureFixture) -> None:
    def node(id: int, type: aif.NodeType, text: str) -> ova.Node:
        return {
            "id": id,
            "type": type,
            "text": text,
            "descriptors": {},
            "x": 0,
            "y": 0,
            "w": 0,
            "h": 0,
            "color": "",
            "scheme": "",
            "cqdesc": {},
            "visible": True,
            "participantID": "",
            "imgurl": None,
        }

    claim: ova.Node = {
        **node(1, "I", "A & B"),
        "majorClaim": True,
        "date": "23/03/2019 - 15:57:30",
        "participantID": "7",
    }
    premise = node(2, "I", "C")
    scheme: ova.Node = {
        **node(3, "RA", "ExpertOpinion"),
        "descriptors": {"s_Conclusion": 1, "s_Premise": 2, "s_Other": None},
    }
    locution = node(4, "L", "Bob: C")
    obj: ova.Graph = {
        "nodes": [claim, premise, scheme, locution],
        "edges": [
            {
                "from": premise,
                "to": scheme,
                "visible": True,
                "date": "06/03/2019 - 14:31:23",
            },
            {"from": scheme, "to": claim, "visible": True},
            {"from": locution, "to": premise, "visible": True},
        ],
        "participants": [{"id": 7, "firstname": "Bob", "surname": "Smith"}],
        "analysis": {
            "txt": '  \U0001f600<span id="node1">A &amp; B</span><br><span id="node2">C</span>',
            "plain_txt": "differs",
            "annotatorName": "",
            "documentDate": "01/02/2020",
        },
    }
    g = ag.load.dict(obj)
    resource = next(iter(g.resources.values()))

    assert resource.text == "  \U0001f600A & B\nC"
    assert resource.timestamp == datetime(2020, 2, 1, tzinfo=UTC)
    assert resource.title is None

    for atom in g.atom_nodes.values():
        assert (reference := atom.reference) and reference.offset is not None
        assert resource.text[reference.offset :].startswith(reference.text)

    assert g.major_claim == "1"
    assert g.atom_nodes["1"].participant == "7"
    assert g.atom_nodes["1"].reference == ag.Reference(
        "A & B", resource=resource.id, offset=3
    )
    assert g.atom_nodes["2"].participant is None
    assert g.atom_nodes["1"].metadata.created == datetime(
        2019, 3, 23, 15, 57, 30, tzinfo=UTC
    )
    assert g.scheme_nodes["3"].premise_descriptors == ("2",)
    assert g.scheme_nodes["3"].label == "Support: Expert Opinion"
    assert len(g.edges) == 2
    assert not g.analysts
    assert [p.name for p in g.participants.values()] == ["Bob Smith"]
    edge = next(iter(g.edges.values()))

    assert (
        edge.metadata.created
        == edge.metadata.updated
        == datetime(2019, 3, 6, 14, 31, 23, tzinfo=UTC)
    )
    assert edge.userdata == {}

    obj = {**obj, "nodes": [{**claim, "participantID": "missing"}]}
    graph = ag.load.ova(obj)

    assert graph.atom_nodes["1"].participant is None
    assert "unknown participant 'missing'" in caplog.text


def test_numeric_ids() -> None:
    for value in (-(2**53 - 1), 0, 2**53 - 1):
        assert stringify_id(value) == str(value)

    assert stringify_id("9007199254740992") == "9007199254740992"

    for value in (-(2**53), 2**53, 1e21, 1.5, True):
        with pytest.raises(ValueError, match="safe integer"):
            stringify_id(value)


def test_dict_argdown():
    g = ag.load.dict(
        {"statements": {}, "arguments": {}, "relations": [], "frontMatter": None},
        "name",
    )

    assert g.name == "name"
    assert not g.nodes
    assert g.userdata == {}


def test_html():
    # the first opened span wins for duplicate ids, unclosed spans end with the text
    text, spans = parse_html(
        '<span id="a" id="b">x<span id="a">y</span><span id="c">&lt;<br>z</span></span>'
        '<span id="d"><b>w</b>'
    )

    assert text == "xy<\nzw"
    assert spans == {"a": Span("xy<\nz", 0), "c": Span("<\nz", 2), "d": Span("w", 5)}


def test_casebase(tmp_path: Path):
    aif = tmp_path / "cb" / "format=aif"
    other = tmp_path / "cb" / "format=other"
    aif.mkdir(parents=True)
    other.mkdir()
    (aif / "case.json").write_text('{"nodes": [], "edges": [], "locutions": []}')
    (aif / "case.txt").write_text("text")
    (other / "case.txt").write_text("text")

    def load(*filters: ag.load.CasebaseFilter) -> list[str]:
        graphs = ag.load.casebase(filters, basepath=tmp_path)

        return [str(path.relative_to(tmp_path)) for path in graphs]

    assert load(ag.load.CasebaseFilter("cb")) == ["cb/format=aif/case.json"]
    assert load(ag.load.CasebaseFilter("c")) == []
    assert load(ag.load.CasebaseFilter("cb", kwargs={"format": "ai"})) == []
    assert load(ag.load.CasebaseFilter("cb", kwargs={"lang": ".*"})) == []


def test_dump_file(tmp_path: Path):
    g = ag.Graph("name")
    ag.dump.file(g, tmp_path / "graph.v2")
    ag.dump.file(g, tmp_path)

    assert {path.name for path in tmp_path.iterdir()} == {"graph.v2", "name.json"}

    for name in (None, "A/B testing?", ".."):
        with pytest.raises(ValueError, match="file name"):
            ag.dump.file(ag.Graph(name), tmp_path)


def test_dump_d2():
    g = ag.GraphDraft()
    g.add_node(ag.AtomNode("a\nb $x", id="$"))

    assert (d2 := ag.dump.d2(g.freeze())) and d2.nodes[0].label == "a b $x"
    assert str(d2).startswith('"\\$": {\nlabel: "a b \\$x"\n')


def test_dump_networkx():
    g = ag.GraphDraft()
    atom, scheme = ag.AtomNode("a"), ag.SchemeNode(ag.Support.DEFAULT)
    g.add_node(atom)
    g.add_node(scheme)
    g.add_edge(ag.Edge(atom.id, scheme.id))
    gnx = ag.dump.networkx(g.freeze(), scheme_attrs={"kind": lambda node: node.label})

    assert gnx.nodes[scheme.id] == {"label": "Support", "kind": "Support"}
    assert gnx.nodes[atom.id] == {"label": "a"}


def test_protobuf_unknown_scheme():
    proto = graph_pb2.Graph(
        nodes={
            "s": graph_pb2.Node(
                scheme=graph_pb2.Scheme(support=graph_pb2.Support.ValueType(999))
            )
        }
    )

    with pytest.raises(ValueError, match="unknown scheme"):
        ag.load.protobuf(proto)
