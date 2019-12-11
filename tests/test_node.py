import pytest
import json
import recap_argument_graph as ag
import pendulum


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
        119935,
        "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.",
        ag.NodeCategory.I,
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
        119935,
        656,
        317,
        "b",
        "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.",
        None,
        None,
        114,
        "",
        ag.NodeCategory.I,
        0,
        {},
        {},
        True,
        "",
        "",
        pendulum.datetime(2019, 3, 6, 14, 31, 23),
        0,
        200,
        90,
        False,
        None,
        None,
    )
]


@pytest.mark.parametrize("data,key,text,category,date", aif_data)
def test_aif_node(data, key, text, category, date):
    data_json = json.loads(data)
    node = ag.Node.from_aif(data_json)

    assert node.key == key
    assert node.text == text
    assert node.category == category
    assert node.date == date

    export = node.to_aif()
    assert export.items() >= data_json.items()


@pytest.mark.parametrize(
    "data,key,x,y,color,text,text_begin,text_end,text_length,comment,category,scheme,descriptors,cqdesc,visible,imgurl,annotator,date,participant_id,w,h,major_claim,is_check_worthy,source",
    ova_data,
)
def test_ova_node(
    data,
    key,
    x,
    y,
    color,
    text,
    text_begin,
    text_end,
    text_length,
    comment,
    category,
    scheme,
    descriptors,
    cqdesc,
    visible,
    imgurl,
    annotator,
    date,
    participant_id,
    w,
    h,
    major_claim,
    is_check_worthy,
    source,
):
    data_json = json.loads(data)
    node = ag.Node.from_ova(data_json)

    assert node.key == key
    assert node.x == x
    assert node.y == y
    assert node.ova_color == color
    assert node.text == text
    assert node.text_begin == text_begin
    assert node.text_end == text_end
    assert node.text_length == text_length
    assert node.comment == comment
    assert node.category == category
    assert node.scheme == scheme
    assert node.descriptors == descriptors
    assert node.cqdesc == cqdesc
    assert node.visible == visible
    assert node.imgurl == imgurl
    assert node.annotator == annotator
    assert node.date == date
    assert node.participant_id == participant_id
    assert node.w == w
    assert node.h == h
    assert node.major_claim == major_claim
    assert node.is_check_worthy == is_check_worthy
    assert node.source == source

    export = node.to_ova()
    assert export.items() >= data_json.items()
