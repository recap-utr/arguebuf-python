import json
import multiprocessing
import typing as t
from pathlib import Path

import arguebuf as ag
import arguebuf.dt as agdt
import pendulum
from arg_services.graph.v1 import graph_pb2
from deepdiff import DeepDiff

# def test_create_graph(shared_datadir):
#     g = ag.Graph("Test")

#     # agdt.to_ova("10/04/1998 - 07:07:07")
#     # agdt.to_aif("10/04/1998 - 07:07:07")
#     # agdt.from_analysis("10/04/1998")
#     # agdt.to_analysis("10/04/1998 - 07:07:07")

#     p1 = ag.Participant.from_protobuf(
#         "Participant 1",
#         graph_pb2.Participant(
#             name="Participant 1",
#             username="Parti 1",
#             email="Parti1@gmail.com",
#             url="thesenuts",
#             location="Trier",
#             description="Hallo Welt!",
#         ),
#     )
#     r1 = ag.Resource.from_protobuf(
#         "Resource234", graph_pb2.Resource(text="Resource234")
#     )

#     assert isinstance(p1.to_protobuf(), graph_pb2.Participant)
#     n1 = ag.AtomNode(
#         text="Node 1",
#         resource=ag.Reference(r1, 0, "Resource234"),
#         participant=p1,
#     )
#     n2 = ag.SchemeNode(ag.SchemeType.SUPPORT)
#     n3 = ag.AtomNode("Node 3")
#     n4 = ag.SchemeNode(ag.SchemeType.SUPPORT)
#     n5 = ag.AtomNode("Node 5")
#     e12 = ag.Edge(n1, n2)
#     e23 = ag.Edge(n2, n3)
#     e34 = ag.Edge(n3, n4)
#     e45 = ag.Edge(n4, n5)

#     g.add_node(n1)
#     g.add_edge(e12)
#     g.add_edge(e23)
#     g.add_edge(e34)
#     g.add_edge(e45)

#     assert e12.source == n1
#     assert e12.target == n2
#     assert e23.source == n2
#     assert e23.target == n3
#     assert e34.source == n3
#     assert e34.target == n4
#     assert e45.source == n4
#     assert e45.target == n5
#     e12.to_aif()
#     e12 = ag.Edge.from_protobuf(
#         "Edge 1", e12.to_protobuf(), nodes={n1.id: n1, n2.id: n2}
#     )

#     assert len(g.incoming_nodes(n1)) == 0
#     assert len(g.incoming_edges(n1)) == 0
#     assert len(g.incoming_nodes(n3)) == 1
#     assert len(g.incoming_edges(n3)) == 1
#     assert len(g.incoming_edges(n5)) == 1
#     assert len(g.incoming_edges(n5)) == 1

#     assert len(g.outgoing_nodes(n1)) == 1
#     assert len(g.outgoing_edges(n1)) == 1
#     assert len(g.outgoing_nodes(n3)) == 1
#     assert len(g.outgoing_edges(n3)) == 1
#     assert len(g.outgoing_nodes(n5)) == 0
#     assert len(g.outgoing_edges(n5)) == 0

#     assert g.major_claim == n5

#     assert set(g.nodes.values()) == set([n1, n2, n3, n4, n5])

#     assert g.node_distance(n1, n1) == 0
#     assert g.node_distance(n1, n2) == 1
#     assert g.node_distance(n1, n3) == 2
#     assert g.node_distance(n1, n4) == 3
#     assert g.node_distance(n1, n5) == 4
#     assert g.node_distance(n2, n2) == 0
#     assert g.node_distance(n3, n3) == 0
#     assert g.node_distance(n4, n4) == 0
#     assert g.node_distance(n5, n5) == 0
#     assert g.scheme_between(n1, n3) == n2
#     assert g.outgoing_atom_nodes(n1) == set([n3])

#     assert len(g.resources) == 0
#     r2 = ag.Resource(text="Resource", title="Resourca", source="Wikipedia")
#     assert r2.plain_text == "Resource"
#     assert isinstance(r2.to_protobuf(), graph_pb2.Resource)
#     g.add_resource(r2)
#     g.add_resource(ag.Resource("Resource2"))
#     assert len(g.resources) == 2
#     g.atom_nodes
#     g.scheme_nodes
#     g.incoming_nodes(n3)
#     g.incoming_atom_nodes(n2)
#     g.outgoing_nodes(n3)
#     g.outgoing_atom_nodes(n2)
#     g.incoming_edges(n3)
#     g.outgoing_edges(n3)

#     g.major_claim = n5
#     g.major_claim
#     g.add_node(n5)
#     g.remove_node(n4)
#     g.add_node(n4)
#     e4 = "Hallo ich bin keine Kante"
#     g.add_edge(e4)
#     g.add_edge(e12)
#     r10 = "Hallo ich bin keine Quelle"
#     g.add_resource(r10)
#     g.add_resource(r2)
#     g.remove_resource(r10)
#     g.remove_resource(r2)
#     g.remove_resource(r2)
#     p3 = "Hallo ich bin kein Teilnehmer"
#     g.add_participant(p3)
#     g.add_participant(p1)
#     g.remove_participant(p3)
#     g.remove_participant(p1)
#     g.remove_participant(p1)

#     assert g.major_claim == n5
#     assert len(g.participants) == 1
#     g.strip_snodes()

#     ref1 = ag.Reference(resource=r2, offset=1, text="Reference")
#     assert ref1.plain_text == "Reference"
#     assert isinstance(ref1.to_protobuf(), graph_pb2.Reference)
#     # ref2 = ag.data.Reference.from_protobuf(obj = ref1.to_protobuf(), resources= [["Node 1",n1],["Node 2", n2]])

#     assert len(g.atom_nodes) == 3
#     assert len(g.scheme_nodes) == 0
#     assert len(g.nodes) == 3
#     assert len(g.edges) == 2
#     ag.render(g.to_gv(), shared_datadir / "output" / "test_create_graph.pdf")
#     g.remove_node(n1)
#     assert len(g.nodes) == 2
#     g.to_protobuf()
#     assert isinstance(g.to_protobuf(), graph_pb2.Graph)

#     # Nachfolgende Änderungen konnte ich aufgrund mangelnden Kenntnisse nicht durchführen in der nötigen Komplexität:
#     # für Test muss jede Eigenschaft mit sinnvollem Argument gefüllt sein, weil sonst scheinbar manche Aktivierung nicht gemacht wird...
#     # from_ova() einfügen
#     # from_aif() einfügen
#     # from_protobuf() einfügen
#     # from_dict() einfügen
#     # from_json() einfügen
#     # to_json() einfügen
#     # from_brat() einfügen
#     # from_io() einfügen
#     # to_io() einfügen
#     # from_file() einfügen
#     # to_file() einfügen
#     # from_folder() einfügen
#     # to_gv() einfügen
#     # copy() einfügen
#     # render() einfügen


def test_import_graphs(shared_datadir):
    brat_folder = shared_datadir / "brat"
    aif_folder = shared_datadir / "aif"
    ova_folder = shared_datadir / "ova"
    kialo_folder = shared_datadir / "kialo"

    with multiprocessing.Pool() as pool:
        pool.map(_import_generic_graph, sorted(aif_folder.rglob("*.json")))
        pool.map(_import_generic_graph, sorted(ova_folder.rglob("*.json")))
        pool.map(_import_generic_graph, sorted(brat_folder.rglob("*.ann")))
        pool.map(_import_generic_graph, sorted(kialo_folder.rglob("*.txt")))

        pool.map(_import_aif_graph, sorted(aif_folder.rglob("*.json")))

    # For debugging
    # for file in sorted(aif_folder.rglob("*.json")):
    #     _import_aif_graph(file)


def _import_generic_graph(file):
    graph = ag.Graph.from_file(file)

    assert graph.to_dict(ag.GraphFormat.AIF) != {}
    assert graph.to_dict(ag.GraphFormat.ARGUEBUF) != {}
    assert graph.to_gv() is not None
    assert graph.to_nx() is not None


def _clean_raw_aif(g: t.MutableMapping[str, t.Any]) -> None:
    # Remove locutions as these are not parsed
    g["locutions"] = []
    g["nodes"] = [node for node in tuple(g["nodes"]) if node["type"] != "L"]
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


def _import_aif_graph(file):
    with file.open() as f:
        raw = json.load(f)

    _clean_raw_aif(raw)

    graph = ag.Graph.from_file(file)
    export = graph.to_dict(ag.GraphFormat.AIF)
    _clean_exported_aif(export)

    # assert export == raw, file # for debugging
    diff = DeepDiff(raw, export, ignore_order=True)

    if diff != {}:
        print("RAW:")
        print(json.dumps(raw))
        print("EXPORT:")
        print(json.dumps(export))
        print()

    assert diff == {}, file
