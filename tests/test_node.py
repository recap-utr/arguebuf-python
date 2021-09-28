import pytest
import json
import arguebuf as ag
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


@pytest.mark.parametrize("data,text,category,date", aif_data)
def test_aif_node(data, text, category, date):
    data_json = json.loads(data)
    node = ag.Node.from_aif(data_json)

    assert node.text == text
    assert node.category == category 
    assert node.date == date

    #export = node.to_aif() ##same as below: is this still needed?
    #assert export.items() >= data_json.items()


@pytest.mark.parametrize(
    "data,color,text,category,descriptors,date,source",
    ova_data,
)
def test_ova_node(
    data,
    color,
    text,
    category,
    descriptors,
    date,
    source,
):
    data_json = json.loads(data)
    node = ag.Node.from_ova(data_json)

    assert node.ova_color == color #Color is no property anymore but it is generated based on "category" -> deletable?
    assert node.text == text
    assert node.category == category #Is the "category" translated into "SchemeNode/AtomNode" or completely useless -> deletable?
    assert node.descriptors == None
    assert node.created == date
    assert node.participant_id == participant_id #Is this randomly generated -> uncheckable aswell?
    #assert node.major_claim == major_claim ##Node does not have a "major_claim"-attribute -> not checkable -> deletable?
    assert node.reference == source
    assert node.metadata == None

    #export = node.to_ova()
    #assert export.items() >= data_json.items()
