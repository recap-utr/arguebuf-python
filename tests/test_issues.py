import json
from collections.abc import Iterable
from pathlib import Path

import pytest
from pydantic import Field, ValidationError

import arguebuf as ag

SOURCE = "Cats 🐈 are the best pets. They are “independent”, and they are clean."
MALFORMED = json.loads(Path("data/malformed.json").read_text(encoding="utf-8"))


def codes(issues: list[ag.Issue]) -> list[str]:
    return [issue.code for issue in issues]


def test_locate() -> None:
    for near in (0, 1):
        assert ag.locate("AAAAAA", "aaaaa", near=near) == ag.Match(near, "AAAAA", 1)
        match = ag.locate("ABXDEABXDE", "abcde", near=near * 5, threshold=0.8)
        assert match is not None and match.offset == near * 5

    assert ag.locate(SOURCE, "are the best pets") == ag.Match(7, "are the best pets", 1)
    assert ag.locate(SOURCE, 'They are "independent".') == ag.Match(
        26, "They are “independent", 1
    )

    match = ag.locate(SOURCE, "they  are clen")

    assert match is not None
    assert (match.offset, match.text) == (54, "they are clean")
    assert (located := ag.locate(SOURCE, "they are", near=50)) is not None
    assert located.offset == 54
    assert ag.locate(SOURCE, "dogs bark loudly") is None


def test_load_repairs() -> None:
    issues: list[ag.Issue] = []
    graph = ag.load.dict(MALFORMED, on_issue=issues.append)

    assert codes(issues) == [
        "duplicate-id",
        "parallel-edge",
        "self-loop",
        "atom-edge",
        "unknown-element",
    ]
    assert all(issue.severity == "warning" for issue in issues)
    assert graph.outgoing_atom_nodes("4") == {graph.nodes["1"]}
    assert codes(ag.check(graph)) == [
        "scheme-without-premise",
        "scheme-without-conclusion",
        "untyped-scheme",
        "no-major-claim",
    ]

    with pytest.raises(ag.GraphError):
        ag.load.dict(MALFORMED, strict=True)


def test_invalid_input() -> None:
    node = {"nodeID": 1, "text": "a", "type": "I"}

    with pytest.raises(ag.GraphError) as info:
        ag.load.dict({"nodes": [{"nodeID": 1, "type": "I"}], "edges": []})

    assert info.value.issue.code == "invalid-input"
    assert info.value.issue.severity == "error"
    assert (
        info.value.issue.hint
        == "Check the input against the specification of its format."
    )
    assert str(info.value) == "The AIF input is invalid: nodes.0.text: Field required"

    with pytest.raises(ag.GraphError, match=r"nodes\.0\.nodeID: .*valid string"):
        ag.load.dict({"nodes": [{**node, "nodeID": True}], "edges": []}, strict=False)

    assert ag.load.dict({"nodes": [node], "edges": []}).atom_nodes.keys() == {"1"}

    with pytest.raises(ag.GraphError, match="not a JSON object"):
        ag.load.dict(json.loads("null"))


def test_unread_and_lenient_fields() -> None:
    issues: list[ag.Issue] = []
    graph = ag.load.dict(
        {
            "nodes": [
                {"nodeID": 1, "text": "a", "type": "I"},
                {"nodeID": 2, "text": "b", "type": "unknown"},
                {"nodeID": 3, "text": "c", "type": "L"},
            ],
            "edges": [
                {"edgeID": 1, "fromID": 2, "toID": 1},
                {"edgeID": 2, "fromID": 3, "toID": 1},
            ],
        },
        on_issue=issues.append,
    )

    assert graph.atom_nodes.keys() == {"1"}
    assert [(i.code, i.message, i.elements) for i in issues] == [
        ("unknown-element", "Skipping node '2' of unknown type 'unknown'.", ("2",))
    ]

    ova = ag.load.dict(
        {
            "analysis": {},
            "participants": [],
            "edges": [],
            "nodes": [{"id": 1, "text": "a", "type": "I", "x": "bad"}],
        }
    )

    assert ova.atom_nodes["1"].participant is None


def test_check() -> None:
    resource = ag.Resource(SOURCE, id="r")
    g = ag.GraphDraft()
    g.add_resource(resource)
    nodes = (
        ag.AtomNode("Cats are the best pets", id="mc"),
        ag.AtomNode(
            "x", reference=ag.Reference("pets", resource="r", offset=1), id="a"
        ),
        ag.AtomNode("y", id="b"),
        ag.AtomNode("z", reference=ag.Reference("dogs", resource="r"), id="o"),
        ag.SchemeNode(ag.Support.DEFAULT, id="s1"),
        ag.SchemeNode(id="s2"),
        ag.SchemeNode(ag.Attack.DEFAULT, id="s3"),
    )

    for node in nodes:
        g.add_node(node)

    for source, target in (("a", "s1"), ("s1", "mc"), ("s1", "b"), ("s2", "s3")):
        g.add_edge(ag.Edge(source, target))

    g.major_claim = "mc"

    assert [(issue.code, issue.elements[0]) for issue in ag.check(g.freeze())] == [
        ("reference-mismatch", "a"),
        ("reference-unresolved", "o"),
        ("scheme-multiple-conclusions", "s1"),
        ("untyped-scheme", "s2"),
        ("scheme-without-premise", "s2"),
        ("scheme-without-premise", "s3"),
        ("scheme-without-conclusion", "s3"),
        ("orphaned-atom", "o"),
        ("disconnected", "mc"),
        ("unreachable-major-claim", "b"),
    ]
    assert ag.check(ag.Graph()) == []


def _paths(
    issues: Iterable[ag.Issue],
) -> list[tuple[str, tuple[str | int, ...] | None]]:
    return [(issue.code, issue.path) for issue in issues]


def _schemes(graph: ag.Graph) -> list[dict[str, object]]:
    return [
        item.model_dump(exclude_defaults=True) for item in ag.outline(graph).schemes
    ]


def test_apply_patch() -> None:
    empty = ag.Graph()
    result = ag.apply_patch(
        empty,
        {
            "resources": [{"id": "r", "text": SOURCE}],
            "atoms": [
                {"id": "mc", "text": "Cats are the best pets."},
                {"id": "p", "text": "they are independant"},
                {"id": "u", "text": "Cats scratch furniture"},
                {"id": "c", "text": "they are clean"},
            ],
            "schemes": [
                {
                    "id": "s",
                    "type": "support",
                    "scheme": "Expert Opinion",
                    "premises": ["p"],
                    "conclusion": "mc",
                },
                {"id": "x", "type": "attack", "premises": ["u"], "conclusion": "s"},
                {"id": "y", "type": "support", "premises": ["c"], "conclusion": "mc"},
            ],
            "majorClaim": "mc",
        },
    )
    graph = result.graph

    assert not empty.nodes
    assert _paths(result.issues) == [
        ("reference-mismatch", ("atoms", 1)),
        ("reference-unresolved", ("atoms", 2)),
    ]
    assert result.created == ("mc", "p", "u", "c", "s", "x", "y", "r")
    assert graph.atom_nodes["mc"].reference == ag.Reference(
        "Cats 🐈 are the best pets", resource="r", offset=0
    )
    assert ag.check(graph) == []
    assert _schemes(graph) == [
        {
            "id": "s",
            "type": "support",
            "scheme": "Expert Opinion",
            "premises": ("p",),
            "conclusion": "mc",
        },
        {"id": "x", "type": "attack", "premises": ("u",), "conclusion": "s"},
        {"id": "y", "type": "support", "premises": ("c",), "conclusion": "mc"},
    ]

    failed = ag.apply_patch(
        graph,
        ag.Patch(
            delete=("c",),
            atoms=(ag.AtomPatch(id="s", text="Wrong kind"),),
            schemes=(
                ag.SchemePatch(
                    id="z", type="support", premises=("missing",), conclusion="mc"
                ),
            ),
        ),
    )

    assert failed.graph is graph
    assert failed.created == failed.updated == failed.removed == ()
    assert _paths(failed.issues) == [
        ("invalid-patch", ("atoms", 0)),
        ("unknown-element", ("schemes", 0)),
    ]

    edited = ag.apply_patch(
        graph,
        {
            # the scheme of p is already removed together with p
            "delete": ["p", "s"],
            "atoms": [{"id": "c", "text": "They are clean"}],
            "schemes": [
                {
                    "id": "y",
                    "type": "attack",
                    "scheme": "Unknown Label",
                    "premises": ["c", "u"],
                    "conclusion": "mc",
                }
            ],
        },
    )

    # unknown scheme labels fall back to the default
    assert _paths(edited.issues) == [("unknown-scheme", ("schemes", 0))]
    # the scheme without premise and its undercutter are removed
    assert list(edited.graph.nodes) == ["mc", "u", "c", "y"]
    assert (edited.created, edited.updated, edited.removed) == (
        (),
        ("c", "y"),
        ("p", "s", "x"),
    )
    assert _schemes(edited.graph) == [
        {"id": "y", "type": "attack", "premises": ("c", "u"), "conclusion": "mc"}
    ]
    assert edited.graph.major_claim == "mc"
    assert "p" in graph.nodes


def test_patch_namespaces() -> None:
    graph = ag.Graph(resources=[ag.Resource("", id="a")])
    added = ag.apply_patch(graph, {"atoms": [{"id": "a", "text": "Claim"}]})

    assert (added.created, added.updated, added.removed) == (("a",), (), ())
    edited = ag.apply_patch(added.graph, {"atoms": [{"id": "a", "text": "Changed"}]})
    assert (edited.created, edited.updated, edited.removed) == ((), ("a",), ())
    removed = ag.apply_patch(added.graph, {"clear": True})
    assert (removed.created, removed.updated, removed.removed) == ((), (), ("a",))
    cleared = ag.apply_patch(added.graph, {"clear": True, "delete": ["a"]})
    assert (cleared.issues, cleared.removed) == ((), ("a",))
    unknown = ag.apply_patch(added.graph, {"clear": True, "delete": ["x"]})
    assert _paths(unknown.issues) == [("unknown-element", ("delete",))]


def test_patch_validation() -> None:
    result = ag.apply_patch(
        ag.Graph(),
        {
            "atoms": [{"id": "a"}],
            "schemes": [
                {"id": "s", "type": "rebut", "premises": [], "conclusion": "a"}
            ],
            "extra": True,
        },
    )

    assert not result.graph.nodes
    assert _paths(result.issues) == [
        ("invalid-patch", ("atoms", 0, "text")),
        ("invalid-patch", ("schemes", 0, "type")),
        ("invalid-patch", ("schemes", 0, "premises")),
        ("invalid-patch", ("extra",)),
    ]

    class Extended(ag.Patch):
        confidence: float = Field(ge=0, le=1)

    assert Extended.model_json_schema()["required"] == ["confidence"]
    with pytest.raises(ValidationError):
        Extended(confidence=2)


def test_graph_edits() -> None:
    g = ag.GraphDraft()
    g.add_resource(ag.Resource("Text", id="r"))
    g.add_node(ag.AtomNode("P", id="p"))
    g.add_node(ag.AtomNode("C", id="c"))
    g.add_node(ag.AtomNode("Q", id="q"))
    scheme = g.link("p", "c")

    assert scheme is not None and scheme.scheme is None
    assert g.link("q", scheme) is None
    assert [node.id for node in g.premise_nodes(scheme)] == ["p", "q"]

    created = g.atom_nodes["p"].metadata
    g.update_atom("p", text="Premise")

    assert g.atom_nodes["p"].metadata.updated > created.updated
    g.update_atom("p", metadata=created)
    assert g.atom_nodes["p"].metadata == created

    # a repeated id was removed by its first occurrence
    result = ag.apply_patch(g.freeze(), {"delete": ["r", "r", "c"]})

    assert result.issues == ()
    assert result.removed == ("c", scheme.id, "r")
