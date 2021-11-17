import json
from typing import Dict

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

@pytest.mark.parametrize("data,id,text,type,date", aif_data_AtomNode)
def test_aif_node_AN(data, id, text, type, date):
    data_json = json.loads(data)
    node = ag.AtomNode.from_aif(data_json)
    
    assert node.id == id
    assert node.text == text
    assert isinstance(node, type)
    assert node.created == date
    assert node.updated == date
    assert node.reference is None
    assert node.metadata == {}
    assert isinstance(node.to_aif(), Dict)
    assert isinstance(node.to_protobuf(), graph_pb2.Node)
    #node3 = ag.AtomNode.from_protobuf("123",node.to_protobuf(),{},{}, )

    ag.utils.text2argumentation_scheme("Rule")
    ag.utils.text2argumentation_scheme("")
    ag.utils.argumentation_scheme2text(graph_pb2.SCHEME_VALUES)
    ag.utils.argumentation_scheme2text(None)

    ag.utils.class_repr(node, {})
    ag.utils.parse("",{})
    ag.utils.parse(None,{})
    ag.utils.duplicate_key_error("","")

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
    assert node.created == date
    assert node.updated == date
    assert node.reference is None
    assert node.metadata == {}

'''
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

@pytest.mark.parametrize("data,id,text,type,date", aif_data_SchemeNode)
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
    assert isinstance(node2.to_protobuf(), graph_pb2.Node)

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
'''