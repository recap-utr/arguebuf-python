import json

import pendulum
import pytest
from arg_services.graph.v1 import graph_pb2

import arguebuf as ag
from arguebuf.converters.argdown import edge_from_argdown

aif_data = [
    (
        """
        {
			"edgeID": "160913",
			"fromID": "119935",
			"toID": "119940",
			"formEdgeID": null
		}
        """,
        "160913",
        "119935",
        "119940",
    )
]


ova_data = [
    (
        """
        {
            "from": {
                "id": 119935,
                "x": 656,
                "y": 317,
                "color": "b",
                "text": "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.",
                "text_begin": [],
                "text_end": [],
                "text_length": [
                114
                ],
                "comment": "",
                "type": "I",
                "scheme": "0",
                "descriptors": {},
                "cqdesc": {},
                "visible": true,
                "imgurl": "",
                "annotator": "",
                "date": "06/03/2019 - 14:31:23",
                "participantID": "0",
                "w": 200,
                "h": 90,
                "majorClaim": false,
                "is_check_worthy": "no",
                "source": ""
            },
            "to": {
                "id": 119940,
                "x": 709,
                "y": 268,
                "color": "g",
                "text": "Sign",
                "text_begin": [],
                "text_end": [],
                "text_length": [],
                "comment": "",
                "type": "RA",
                "scheme": "30",
                "descriptors": {
                    "s_General Premise։ B is generally indicated as true when its sign, A, is true": null,
                    "s_Specific Premise։ A a finding A is true in this situation": 119935,
                    "s_Conclusion։ B is true in this situation": 119937,
                    "s_Expert Opinion։ Expert E asserts that proposition A is true/false": null
                },
                "cqdesc": {},
                "visible": true,
                "imgurl": "",
                "annotator": "Anna Ludwig",
                "date": "23/03/2019 - 15:54:34",
                "participantID": "0",
                "w": 52,
                "h": 30,
                "majorClaim": false,
                "is_check_worthy": "no",
                "source": ""
            },
            "visible": true,
            "annotator": "",
            "date": "06/03/2019 - 14:31:23"
            }
        """,
        "119935",
        "119940",
        pendulum.datetime(2019, 3, 6, 14, 31, 23),
    )
]

sadface_data = [
    (
        """
        {
            "id": "3df54ae1-fa41-4ac7-85d5-4badee39215b",
            "source_id": "70447169-9264-41dc-b8e9-50523f8368c1",
            "target_id": "ae3f0c7f-9f69-4cab-9db3-3b9c46f56e09"
        }
        """,
        "3df54ae1-fa41-4ac7-85d5-4badee39215b",
        "70447169-9264-41dc-b8e9-50523f8368c1",
        "ae3f0c7f-9f69-4cab-9db3-3b9c46f56e09",
    )
]

argdown_json_data = [
    (
        """
        {
            "id": "e1",
            "type": "map-edge",
            "relationType": "support",
            "from": "n2",
            "to": "n0",
            "toEquivalenceClass": "Statement 1"
        }
        """,
        "e1",
        "n2",
        "n0",
    )
]


@pytest.mark.parametrize("data,id,start,end", argdown_json_data)
def test_argdown_json_edge(data, id, start, end):
    data_json = json.loads(data)
    edge = edge_from_argdown(
        data_json,
        {
            start: ag.AtomNode(id=start, text=""),
            end: ag.AtomNode(id=end, text=""),
        },
    )

    assert edge
    assert edge.id == id
    assert isinstance(edge.source, ag.AtomNode)
    assert isinstance(edge.target, ag.AtomNode)
    assert edge.source.id == start
    assert edge.target.id == end
    assert edge.metadata is not None
    assert edge.userdata == {}
    assert isinstance(edge.to_protobuf(), graph_pb2.Edge)


@pytest.mark.parametrize("data,id,start,end", sadface_data)
def test_sadface_edge(data, id, start, end):
    data_json = json.loads(data)
    edge = ag.Edge.from_sadface(
        data_json,
        {
            start: ag.AtomNode(id=start, text=""),
            end: ag.AtomNode(id=end, text=""),
        },
    )

    assert edge
    assert edge.id == id
    assert isinstance(edge.source, ag.AtomNode)
    assert isinstance(edge.target, ag.AtomNode)
    assert edge.source.id == start
    assert edge.target.id == end
    assert edge.metadata is not None
    assert edge.userdata == {}
    assert isinstance(edge.to_protobuf(), graph_pb2.Edge)


@pytest.mark.parametrize("data,id,start,end", aif_data)
def test_aif_edge(data, id, start, end):
    data_json = json.loads(data)
    edge = ag.Edge.from_aif(
        data_json,
        {
            start: ag.AtomNode(id=start, text=""),
            end: ag.AtomNode(id=end, text=""),
        },
    )

    assert edge
    assert edge.id == id
    assert isinstance(edge.source, ag.AtomNode)
    assert isinstance(edge.target, ag.AtomNode)
    assert edge.source.id == start
    assert edge.target.id == end
    assert edge.metadata is not None
    assert edge.userdata == {}
    assert isinstance(edge.to_protobuf(), graph_pb2.Edge)


@pytest.mark.parametrize("data,start,end,date", ova_data)
def test_ova_edge(data, start, end, date):
    data_json = json.loads(data)
    edge = ag.Edge.from_ova(
        data_json,
        {
            start: ag.AtomNode(id=start, text=""),
            end: ag.AtomNode(id=end, text=""),
        },
    )

    assert edge
    assert isinstance(edge.id, str)
    assert isinstance(edge.source, ag.AtomNode)
    assert isinstance(edge.target, ag.AtomNode)
    assert edge.source.id == start
    assert edge.target.id == end
    assert edge.metadata.created == date
    assert edge.metadata.updated == date
    assert edge.userdata == {}
    assert isinstance(edge.to_protobuf(), graph_pb2.Edge)
