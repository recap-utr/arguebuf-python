import json
from typing import Dict
from enum import Enum
from arguebuf.models.node import Support

import arguebuf as ag
import pendulum
import pytest
from arg_services.graph.v1 import graph_pb2

aif_data_AtomNode = [
    (
        """
        {
            "nodeID": "119935",
            "text": "One can hardly move in Friedrichshain or Neuk\u00f6lln these days without permanently scanning the ground for dog dirt.",
            "type": "I",
            "timestamp": "2015-12-14 12:09:15"
        }
        """,
        "119935",
        "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.",
        ag.AtomNode,
        pendulum.datetime(2015, 12, 14, 12, 9, 15),
    )
]

sadface_data_AtomNode = [
    (
        """
        {
            "id": "6cd219cc-3203-4602-88bd-d3639f86fb37",
            "metadata": {},
            "sources": [],
            "text": "The 'Hang Back' advert does not clearly express the intended message",
            "type": "atom"
        }
        """,
        "6cd219cc-3203-4602-88bd-d3639f86fb37",
        "The 'Hang Back' advert does not clearly express the intended message",
        ag.AtomNode
    )
]

ova_data_AtomNode = [
    (
        """
        {
            "id": 119935,
            "x": 656,
            "y": 317,
            "color": "b",
            "text": "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.",
            "text_begin": [],
            "text_end": [],
            "text_length": [114],
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
            "majorClaim": false
        }
        """,
        "119935",
        "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.",
        ag.AtomNode,
        pendulum.datetime(2019, 3, 6, 14, 31, 23),
    )
]


@pytest.mark.parametrize("data,id,text,type", sadface_data_AtomNode)
def test_sadface_node_AN(data, id, text, type):
    data_json = json.loads(data)
    node = ag.AtomNode.from_sadface(data_json)

    assert node.id == id
    assert node.text == text
    assert isinstance(node, type)
    assert node.reference is None
    assert node.userdata == {}
    assert isinstance(node.to_sadface(), Dict)
    assert isinstance(node.to_protobuf(), graph_pb2.Node)


@pytest.mark.parametrize("data,id,text,type,date", aif_data_AtomNode)
def test_aif_node_AN(data, id, text, type, date):
    data_json = json.loads(data)
    node = ag.AtomNode.from_aif(data_json)

    assert node.id == id
    assert node.text == text
    assert isinstance(node, type)
    assert node.metadata.created == date
    assert node.metadata.updated == date
    assert node.reference is None
    assert node.userdata == {}
    assert isinstance(node.to_aif(), Dict)
    assert isinstance(node.to_protobuf(), graph_pb2.Node)
    # node3 = ag.AtomNode.from_protobuf("123",node.to_protobuf(),{},{}, )


@pytest.mark.parametrize(
    "data,id,text,type,date",
    ova_data_AtomNode,
)
def test_ova_node_AN(data, id, text, type, date):
    data_json = json.loads(data)
    node = ag.AtomNode.from_ova(data_json)

    assert node.id == id
    assert node.text == text
    assert isinstance(node, type)
    assert node.metadata.created == date
    assert node.metadata.updated == date
    assert node.reference is None
    assert node.userdata == {}


aif_data_SchemeNode = [
    (
        """
        {
            "nodeID": "119935",
            "text": "One can hardly move in Friedrichshain or Neuk\u00f6lln these days without permanently scanning the ground for dog dirt.",
            "type": "S",
            "timestamp": "2015-12-14 12:09:15"
        }
        """,
        "119935",
        "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.",
        ag.SchemeNode,
        pendulum.datetime(2015, 12, 14, 12, 9, 15),
    )
]

ova_data_SchemeNode = [
    (
        """
        {
            "id": 119935,
            "x": 656,
            "y": 317,
            "color": "b",
            "text": "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.",
            "text_begin": [],
            "text_end": [],
            "text_length": [114],
            "comment": "",
            "type": "S",
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
            "majorClaim": false
        }
        """,
        "119935",
        "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.",
        ag.SchemeNode,
        pendulum.datetime(2019, 3, 6, 14, 31, 23),
    )
]

sadface_data_SchemeNode = [
    (
        """
        {
            "id": "70447169-9264-41dc-b8e9-50523f8368c1",
            "metadata": {},
            "name": "Support",
            "type": "scheme"
        }
        """,
        "70447169-9264-41dc-b8e9-50523f8368c1",
        ag.SchemeNode,
        Support
    )
]


@pytest.mark.parametrize("data,id,type,name", sadface_data_SchemeNode)
def test_sadface_node_SN(data, id, type, name):
    data_json = json.loads(data)
    node = ag.SchemeNode.from_sadface(data_json)

    assert node.id == id
    assert isinstance(node, type)
    assert node.scheme == name
    assert isinstance(node.metadata, ag.Metadata)
    assert isinstance(node.to_protobuf(), graph_pb2.Node)


"""@pytest.mark.parametrize("data,id,text,type,date", aif_data_SchemeNode)
def test_aif_node_SN(data, id, text, type, date):
    data_json = json.loads(data)
    node2 = ag.SchemeNode.from_aif(data_json)

    assert node2.id == id
    assert node2.text == text
    assert isinstance(node2, type)
    assert node2.created == date
    assert node2.updated == date
    assert node2.reference is None
    assert node2.metadata == {}
    assert isinstance(node2.to_aif(), Dict)
    assert isinstance(node2.to_protobuf(), graph_pb2.Node)"""

"""

@pytest.mark.parametrize(
    "data,id,text,type,date",
    ova_data_SchemeNode,
)
def test_ova_node_SN(data, id, text, type, date):
    data_json = json.loads(data)
    node2 = ag.SchemeNode.from_ova(data_json)

    assert node2.id == id
    assert node2.text == text
    assert isinstance(node2, type)
    assert node2.created == date
    assert node2.updated == date
    assert node2.reference is None
    assert node2.metadata == {}

"""
