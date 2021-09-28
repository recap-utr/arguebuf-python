import pytest
import json
import arguebuf as ag
import pendulum


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
        160913,
        119935,
        119940,
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
        119935,
        119940,
        True,
        "",
        pendulum.datetime(2019, 3, 6, 14, 31, 23),
    )
]


@pytest.mark.parametrize("data,key,start,end", aif_data)
def test_aif_edge(data, key, start, end):
    data_json = json.loads(data)
    edge = ag.Edge.from_aif(
        data_json,
        {
            start: ag.Node(start, "", ag.NodeCategory.I),
            end: ag.Node(end, "", ag.NodeCategory.I), #is this still correct? or shall I adapt it to "ag.unique_id()" instead of "start"?
        },
    )

    assert edge._source._id == start
    assert edge._target._id == end

    #export = edge.to_aif()
    #assert export == data_json


@pytest.mark.parametrize("data,start,end,visible,date", ova_data)
def test_ova_edge(data, start, end, visible, date):
    data_json = json.loads(data)
    edge = ag.Edge.from_ova(data_json, 1)

    assert isinstance(edge.source, ag.Node)
    assert isinstance(edge.target, ag.Node)
    assert edge._source._id == start #are these still checkable or deletable
    assert edge._target._id == end  #due to randomization of id?
    assert edge.created == date
    assert edge.updated == None #Same as with metadata
    assert edge.metadata == None #Metadata-tests shall test on "None" or on "{}" since the last one is actually performed while creation from another formate...


    #export = edge.to_ova()
    #assert export == data_json
