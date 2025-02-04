import json
import typing as t
from pathlib import Path

from deepdiff.diff import DeepDiff

import arguebuf as ag

ARGUEBASE = Path("data", "arguebase")


# def test_convert_kialo():
#     graphs = ag.load.casebase(
#         ag.load.CasebaseFilter("kialo", r"^the-"),
#         basepath=ARGUEBASE_PRIVATE,
#     )
#     assert len(graphs) == 27

#     for graph in graphs.values():
#         _test_generic(graph)


# def test_convert_ova():
#     graphs = ag.load.casebase(
#         ag.load.CasebaseFilter("recap", format="ova", lang="de"),
#         basepath=ARGUEBASE_PRIVATE,
#     )
#     assert len(graphs) == 100

#     for graph in graphs.values():
#         _test_generic(graph)


def test_convert_aif():
    graphs = ag.load.casebase(
        ag.load.CasebaseFilter("microtexts", format="aif"),
        basepath=ARGUEBASE,
    )
    assert len(graphs) == 110

    for file, graph in graphs.items():
        _test_generic(graph)
        _test_aif(graph, file)


def test_convert_arggraph():
    graphs = ag.load.casebase(
        ag.load.CasebaseFilter(
            r"microtexts", r"^micro_[bc]", format="arggraph", lang="en"
        ),
        basepath=ARGUEBASE,
    )
    assert len(graphs) == 62 + 171

    for graph in graphs.values():
        _test_generic(graph)


def _test_generic(graph: ag.Graph):
    assert ag.dump.dict(graph, ag.dump.Config(format=ag.dump.Format.AIF)) != {}
    assert ag.dump.dict(graph, ag.dump.Config(format=ag.dump.Format.ARGUEBUF)) != {}


def _clean_raw_aif(g: t.MutableMapping[str, t.Any]) -> None:
    # Remove locutions as these are not parsed
    g["locutions"] = []
    g["nodes"] = [
        node for node in tuple(g["nodes"]) if node["type"] not in {"L", "TA", "YA"}
    ]
    node_ids = {node["nodeID"] for node in g["nodes"]}
    g["edges"] = [
        edge
        for edge in tuple(g["edges"])
        if edge["fromID"] in node_ids and edge["toID"] in node_ids
    ]

    for node in g["nodes"]:
        if node["type"] != "I":
            # There is a mitchmatch between our export and the araucaria text
            del node["text"]

            # Also, scheme information is exported differently than done in the araucaria corpus.
            # For now, we do not check the correct export of schemes.
            if "scheme" in node:
                del node["scheme"]
            if "schemeID" in node:
                del node["schemeID"]


def _clean_exported_aif(g: t.MutableMapping[str, t.Any]) -> None:
    for node in g["nodes"]:
        if node["type"] != "I":
            assert len(node["text"]) > 1
            del node["text"]


def _test_aif(graph: ag.Graph, file: Path):
    with file.open() as f:
        raw = json.load(f)

    _clean_raw_aif(raw)

    export = ag.dump.dict(graph, ag.dump.Config(format=ag.dump.Format.AIF))
    _clean_exported_aif(export)

    assert export == raw, file  # for debugging
    diff = DeepDiff(raw, export, ignore_order=True)

    # if diff != {}:
    #     print("RAW:")
    #     print(json.dumps(raw))
    #     print("EXPORT:")
    #     print(json.dumps(export))
    #     print()

    assert diff == {}, file
