import json
import typing as t
from pathlib import Path

from arg_services.graph.v1 import graph_pb2
from deepdiff import DeepDiff

import arguebuf as ag

DATA_PATH = Path("data")


def test_convert_kialo():
    graphs = ag.from_casebase(DATA_PATH, ag.CasebaseFilter(r"kialo", r"^the-"))
    assert len(graphs) == 27

    for graph in graphs.values():
        _test_generic(graph)


def test_convert_recap():
    graphs = ag.from_casebase(DATA_PATH, ag.CasebaseFilter(r"recap", format=r"ova"))
    assert len(graphs) == 100

    for graph in graphs.values():
        _test_generic(graph)


# def test_convert_microtexts():
#     graphs = ag.from_casebase(DATA_PATH, ag.CasebaseFilter(r"microtexts", r"^the-"))
#     assert len(graphs) == 27

#     for graph in graphs.values():
#         _test_generic(graph)


def _test_generic(graph: ag.Graph):
    assert ag.to_dict(graph, ag.GraphFormat.AIF) != {}
    assert ag.to_dict(graph, ag.GraphFormat.ARGUEBUF) != {}


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


def _test_aif(file):
    with file.open() as f:
        raw = json.load(f)

    _clean_raw_aif(raw)

    graph = ag.from_file(file)
    export = ag.to_dict(graph, ag.GraphFormat.AIF)
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
