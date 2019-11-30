import pytest
import json
import argument_graph as ag
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
    edge = ag.Edge.from_aif(
        json.loads(data), {start: ag.Node(start), end: ag.Node(end)}
    )

    assert edge.key == key
    assert edge.start.key == start
    assert edge.end.key == end

    export = edge.to_aif()

    assert export.get("edgeID") == str(key)
    assert export.get("fromID") == str(start)
    assert export.get("toID") == str(end)
    assert export.get("formEdgeID") == None


@pytest.mark.parametrize("data,start,end,visible,annotator,date", ova_data)
def test_ova_edge(data, start, end, visible, annotator, date):
    data_json = json.loads(data)
    edge = ag.Edge.from_ova(data_json)

    assert isinstance(edge.start, ag.Node)
    assert isinstance(edge.end, ag.Node)
    assert edge.start.key == start
    assert edge.end.key == end
    assert edge.visible == visible
    assert edge.annotator == annotator
    assert edge.date == date

    export = edge.to_ova()
    assert export == data_json
