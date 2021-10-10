import json

import arguebuf as ag
import pendulum
import pytest

aif_data = [
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


ova_data = [
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


@pytest.mark.parametrize("data,id,text,type,date", aif_data)
def test_aif_node(data, id, text, type, date):
    data_json = json.loads(data)
    node = ag.AtomNode.from_aif(data_json)

    assert node.id == id
    assert node.text == text
    assert isinstance(node, type)
    assert node.created == date
    assert node.updated == date
    assert node.reference is None
    assert node.metadata == {}


@pytest.mark.parametrize(
    "data,id,text,type,date",
    ova_data,
)
def test_ova_node(data, id, text, type, date):
    data_json = json.loads(data)
    node = ag.AtomNode.from_ova(data_json)

    assert node.id == id
    assert node.text == text
    assert isinstance(node, type)
    assert node.created == date
    assert node.updated == date
    assert node.reference is None
    assert node.metadata == {}
