import pytest
import json
from pathlib import Path
import argument_graph as ag


ova_data = [
    (
        """
        {
            "nodes": [
                {
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
                {
                    "id": 119936,
                    "x": 446,
                    "y": 319,
                    "color": "b",
                    "text": "And when bad luck does strike and you step into one of the many 'land mines' you have to painstakingly scrape the remains off your soles.",
                    "text_begin": [],
                    "text_end": [],
                    "text_length": [
                        137
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
                {
                    "id": 119937,
                    "x": 448,
                    "y": 122,
                    "color": "m",
                    "text": "Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners.",
                    "text_begin": [],
                    "text_end": [],
                    "text_length": [
                        102
                    ],
                    "comment": "",
                    "type": "I",
                    "scheme": "0",
                    "descriptors": {},
                    "cqdesc": {},
                    "visible": true,
                    "imgurl": "",
                    "annotator": "Anna Ludwig",
                    "date": "23/03/2019 - 15:53:31",
                    "participantID": "0",
                    "w": 200,
                    "h": 70,
                    "majorClaim": true,
                    "is_check_worthy": "no",
                    "source": ""
                },
                {
                    "id": 119938,
                    "x": 226,
                    "y": 318,
                    "color": "b",
                    "text": "Of course, first they'd actually need to be caught in the act by public order officers,",
                    "text_begin": [],
                    "text_end": [],
                    "text_length": [
                        87
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
                    "h": 70,
                    "majorClaim": false,
                    "is_check_worthy": "no",
                    "source": ""
                },
                {
                    "id": 119939,
                    "x": 4,
                    "y": 318,
                    "color": "b",
                    "text": "but once they have to dig into their pockets, their laziness will sure vanish!",
                    "text_begin": [],
                    "text_end": [],
                    "text_length": [
                        78
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
                    "h": 70,
                    "majorClaim": false,
                    "is_check_worthy": "no",
                    "source": ""
                },
                {
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
                {
                    "id": 119941,
                    "x": 496,
                    "y": 265,
                    "color": "g",
                    "text": "Negative Consequences",
                    "text_begin": [],
                    "text_end": [],
                    "text_length": [],
                    "comment": "",
                    "type": "RA",
                    "scheme": "22",
                    "descriptors": {
                        "s_Premise։ If A is brought about, then bad consequences will occur": 119936,
                        "s_Conclusion։ Therefore, A should not be brought about": 119937,
                        "s_Expert Opinion։ Expert E asserts that proposition A is true/false": null
                    },
                    "cqdesc": {},
                    "visible": true,
                    "imgurl": "",
                    "annotator": "Anna Ludwig",
                    "date": "23/03/2019 - 15:54:43",
                    "participantID": "0",
                    "w": 143,
                    "h": 30,
                    "majorClaim": false,
                    "is_check_worthy": "no",
                    "source": ""
                },
                {
                    "id": 119942,
                    "x": 279,
                    "y": 270,
                    "color": "r",
                    "text": "Default Conflict",
                    "text_begin": [],
                    "text_end": [],
                    "text_length": [],
                    "comment": "",
                    "type": "CA",
                    "scheme": "71",
                    "descriptors": {},
                    "cqdesc": {},
                    "visible": true,
                    "imgurl": "",
                    "annotator": "Anna Ludwig",
                    "date": "23/03/2019 - 15:53:37",
                    "participantID": "0",
                    "w": 103,
                    "h": 30,
                    "majorClaim": false,
                    "is_check_worthy": "no",
                    "source": ""
                },
                {
                    "id": 119943,
                    "x": 50,
                    "y": 260,
                    "color": "r",
                    "text": "Default Conflict",
                    "text_begin": [],
                    "text_end": [],
                    "text_length": [],
                    "comment": "",
                    "type": "CA",
                    "scheme": "71",
                    "descriptors": {},
                    "cqdesc": {},
                    "visible": true,
                    "imgurl": "",
                    "annotator": "Anna Ludwig",
                    "date": "23/03/2019 - 15:53:41",
                    "participantID": "0",
                    "w": 103,
                    "h": 30,
                    "majorClaim": false,
                    "is_check_worthy": "no",
                    "source": ""
                }
            ],
            "edges": [
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
                },
                {
                    "from": {
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
                    "to": {
                        "id": 119937,
                        "x": 448,
                        "y": 122,
                        "color": "m",
                        "text": "Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners.",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [
                            102
                        ],
                        "comment": "",
                        "type": "I",
                        "scheme": "0",
                        "descriptors": {},
                        "cqdesc": {},
                        "visible": true,
                        "imgurl": "",
                        "annotator": "Anna Ludwig",
                        "date": "23/03/2019 - 15:53:31",
                        "participantID": "0",
                        "w": 200,
                        "h": 70,
                        "majorClaim": true,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "visible": true,
                    "annotator": "",
                    "date": "06/03/2019 - 14:31:23"
                },
                {
                    "from": {
                        "id": 119936,
                        "x": 446,
                        "y": 319,
                        "color": "b",
                        "text": "And when bad luck does strike and you step into one of the many 'land mines' you have to painstakingly scrape the remains off your soles.",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [
                            137
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
                        "id": 119941,
                        "x": 496,
                        "y": 265,
                        "color": "g",
                        "text": "Negative Consequences",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [],
                        "comment": "",
                        "type": "RA",
                        "scheme": "22",
                        "descriptors": {
                            "s_Premise։ If A is brought about, then bad consequences will occur": 119936,
                            "s_Conclusion։ Therefore, A should not be brought about": 119937,
                            "s_Expert Opinion։ Expert E asserts that proposition A is true/false": null
                        },
                        "cqdesc": {},
                        "visible": true,
                        "imgurl": "",
                        "annotator": "Anna Ludwig",
                        "date": "23/03/2019 - 15:54:43",
                        "participantID": "0",
                        "w": 143,
                        "h": 30,
                        "majorClaim": false,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "visible": true,
                    "annotator": "",
                    "date": "06/03/2019 - 14:31:23"
                },
                {
                    "from": {
                        "id": 119941,
                        "x": 496,
                        "y": 265,
                        "color": "g",
                        "text": "Negative Consequences",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [],
                        "comment": "",
                        "type": "RA",
                        "scheme": "22",
                        "descriptors": {
                            "s_Premise։ If A is brought about, then bad consequences will occur": 119936,
                            "s_Conclusion։ Therefore, A should not be brought about": 119937,
                            "s_Expert Opinion։ Expert E asserts that proposition A is true/false": null
                        },
                        "cqdesc": {},
                        "visible": true,
                        "imgurl": "",
                        "annotator": "Anna Ludwig",
                        "date": "23/03/2019 - 15:54:43",
                        "participantID": "0",
                        "w": 143,
                        "h": 30,
                        "majorClaim": false,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "to": {
                        "id": 119937,
                        "x": 448,
                        "y": 122,
                        "color": "m",
                        "text": "Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners.",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [
                            102
                        ],
                        "comment": "",
                        "type": "I",
                        "scheme": "0",
                        "descriptors": {},
                        "cqdesc": {},
                        "visible": true,
                        "imgurl": "",
                        "annotator": "Anna Ludwig",
                        "date": "23/03/2019 - 15:53:31",
                        "participantID": "0",
                        "w": 200,
                        "h": 70,
                        "majorClaim": true,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "visible": true,
                    "annotator": "",
                    "date": "06/03/2019 - 14:31:23"
                },
                {
                    "from": {
                        "id": 119938,
                        "x": 226,
                        "y": 318,
                        "color": "b",
                        "text": "Of course, first they'd actually need to be caught in the act by public order officers,",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [
                            87
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
                        "h": 70,
                        "majorClaim": false,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "to": {
                        "id": 119942,
                        "x": 279,
                        "y": 270,
                        "color": "r",
                        "text": "Default Conflict",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [],
                        "comment": "",
                        "type": "CA",
                        "scheme": "71",
                        "descriptors": {},
                        "cqdesc": {},
                        "visible": true,
                        "imgurl": "",
                        "annotator": "Anna Ludwig",
                        "date": "23/03/2019 - 15:53:37",
                        "participantID": "0",
                        "w": 103,
                        "h": 30,
                        "majorClaim": false,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "visible": true,
                    "annotator": "",
                    "date": "06/03/2019 - 14:31:23"
                },
                {
                    "from": {
                        "id": 119942,
                        "x": 279,
                        "y": 270,
                        "color": "r",
                        "text": "Default Conflict",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [],
                        "comment": "",
                        "type": "CA",
                        "scheme": "71",
                        "descriptors": {},
                        "cqdesc": {},
                        "visible": true,
                        "imgurl": "",
                        "annotator": "Anna Ludwig",
                        "date": "23/03/2019 - 15:53:37",
                        "participantID": "0",
                        "w": 103,
                        "h": 30,
                        "majorClaim": false,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "to": {
                        "id": 119937,
                        "x": 448,
                        "y": 122,
                        "color": "m",
                        "text": "Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners.",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [
                            102
                        ],
                        "comment": "",
                        "type": "I",
                        "scheme": "0",
                        "descriptors": {},
                        "cqdesc": {},
                        "visible": true,
                        "imgurl": "",
                        "annotator": "Anna Ludwig",
                        "date": "23/03/2019 - 15:53:31",
                        "participantID": "0",
                        "w": 200,
                        "h": 70,
                        "majorClaim": true,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "visible": true,
                    "annotator": "",
                    "date": "06/03/2019 - 14:31:23"
                },
                {
                    "from": {
                        "id": 119939,
                        "x": 4,
                        "y": 318,
                        "color": "b",
                        "text": "but once they have to dig into their pockets, their laziness will sure vanish!",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [
                            78
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
                        "h": 70,
                        "majorClaim": false,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "to": {
                        "id": 119943,
                        "x": 50,
                        "y": 260,
                        "color": "r",
                        "text": "Default Conflict",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [],
                        "comment": "",
                        "type": "CA",
                        "scheme": "71",
                        "descriptors": {},
                        "cqdesc": {},
                        "visible": true,
                        "imgurl": "",
                        "annotator": "Anna Ludwig",
                        "date": "23/03/2019 - 15:53:41",
                        "participantID": "0",
                        "w": 103,
                        "h": 30,
                        "majorClaim": false,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "visible": true,
                    "annotator": "",
                    "date": "06/03/2019 - 14:31:23"
                },
                {
                    "from": {
                        "id": 119943,
                        "x": 50,
                        "y": 260,
                        "color": "r",
                        "text": "Default Conflict",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [],
                        "comment": "",
                        "type": "CA",
                        "scheme": "71",
                        "descriptors": {},
                        "cqdesc": {},
                        "visible": true,
                        "imgurl": "",
                        "annotator": "Anna Ludwig",
                        "date": "23/03/2019 - 15:53:41",
                        "participantID": "0",
                        "w": 103,
                        "h": 30,
                        "majorClaim": false,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "to": {
                        "id": 119942,
                        "x": 279,
                        "y": 270,
                        "color": "r",
                        "text": "Default Conflict",
                        "text_begin": [],
                        "text_end": [],
                        "text_length": [],
                        "comment": "",
                        "type": "CA",
                        "scheme": "71",
                        "descriptors": {},
                        "cqdesc": {},
                        "visible": true,
                        "imgurl": "",
                        "annotator": "Anna Ludwig",
                        "date": "23/03/2019 - 15:53:37",
                        "participantID": "0",
                        "w": 103,
                        "h": 30,
                        "majorClaim": false,
                        "is_check_worthy": "no",
                        "source": ""
                    },
                    "visible": true,
                    "annotator": "",
                    "date": "06/03/2019 - 14:31:23"
                }
            ],
            "participants": [],
            "analysis": {
                "ovaVersion": "1.2.0",
                "txt": "<span class=\\"highlighted\\" id=\\"node119935\\">One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.</span> <span class=\\"highlighted\\" id=\\"node119936\\">And when bad luck does strike and you step into one of the many 'land mines' you have to painstakingly scrape the remains off your soles.</span> <span class=\\"highlighted\\" id=\\"node119937\\">Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners.</span> <span class=\\"highlighted\\" id=\\"node119938\\">Of course, first they'd actually need to be caught in the act by public order officers,</span> <span class=\\"highlighted\\" id=\\"node119939\\">but once they have to dig into their pockets, their laziness will sure vanish!</span><br>",
                "plain_txt": "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt. And when bad luck does strike and you step into one of the many 'land mines' you have to painstakingly scrape the remains off your soles. Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners. Of course, first they'd actually need to be caught in the act by public order officers, but once they have to dig into their pockets, their laziness will sure vanish!\\n",
                "annotatorName": "Anna Ludwig",
                "documentTitle": "nodeset6362.json",
                "documentSource": "",
                "documentDate": "30/11/2019"
            }
        }
        """,
        9,
        8,
        list,
        ag.Analysis,
    )
]


aif_data = [
    (
        """
        {
            "nodes": [
                {
                    "nodeID": "119935",
                    "text": "One can hardly move in Friedrichshain or Neuk\\u00f6lln these days without permanently scanning the ground for dog dirt.",
                    "type": "I",
                    "timestamp": "2015-12-14 12:09:15"
                },
                {
                    "nodeID": "119936",
                    "text": "And when bad luck does strike and you step into one of the many 'land mines' you have to painstakingly scrape the remains off your soles.",
                    "type": "I",
                    "timestamp": "2015-12-14 12:09:15"
                },
                {
                    "nodeID": "119937",
                    "text": "Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners.",
                    "type": "I",
                    "timestamp": "2015-12-14 12:09:15"
                },
                {
                    "nodeID": "119938",
                    "text": "Of course, first they'd actually need to be caught in the act by public order officers,",
                    "type": "I",
                    "timestamp": "2015-12-14 12:09:15"
                },
                {
                    "nodeID": "119939",
                    "text": "but once they have to dig into their pockets, their laziness will sure vanish!",
                    "type": "I",
                    "timestamp": "2015-12-14 12:09:15"
                },
                {
                    "nodeID": "119940",
                    "text": "Default Inference",
                    "type": "RA",
                    "timestamp": "2015-12-14 12:09:15"
                },
                {
                    "nodeID": "119941",
                    "text": "Default Inference",
                    "type": "RA",
                    "timestamp": "2015-12-14 12:09:15"
                },
                {
                    "nodeID": "119942",
                    "text": "Default Conflict",
                    "type": "CA",
                    "timestamp": "2015-12-14 12:09:15"
                },
                {
                    "nodeID": "119943",
                    "text": "Default Conflict",
                    "type": "CA",
                    "timestamp": "2015-12-14 12:09:15"
                }
            ],
            "edges": [
                {
                    "edgeID": "160913",
                    "fromID": "119935",
                    "toID": "119940",
                    "formEdgeID": null
                },
                {
                    "edgeID": "160914",
                    "fromID": "119940",
                    "toID": "119937",
                    "formEdgeID": null
                },
                {
                    "edgeID": "160915",
                    "fromID": "119936",
                    "toID": "119941",
                    "formEdgeID": null
                },
                {
                    "edgeID": "160916",
                    "fromID": "119941",
                    "toID": "119937",
                    "formEdgeID": null
                },
                {
                    "edgeID": "160917",
                    "fromID": "119938",
                    "toID": "119942",
                    "formEdgeID": null
                },
                {
                    "edgeID": "160918",
                    "fromID": "119942",
                    "toID": "119937",
                    "formEdgeID": null
                },
                {
                    "edgeID": "160919",
                    "fromID": "119939",
                    "toID": "119943",
                    "formEdgeID": null
                },
                {
                    "edgeID": "160920",
                    "fromID": "119943",
                    "toID": "119942",
                    "formEdgeID": null
                }
            ],
            "locutions": []
        }
        """,
        9,
        8,
        type(None),
        type(None),
    )
]


mixed_data = aif_data + ova_data


@pytest.mark.parametrize(
    "data,n_nodes,n_edges,type_participants,type_analysis", mixed_data
)
def test_graph(tmp_path, data, n_nodes, n_edges, type_participants, type_analysis):
    data_json = json.loads(data)
    graph = ag.Graph.from_dict(data_json)

    assert len(graph.nodes) == n_nodes
    assert len(graph.edges) == n_edges
    assert isinstance(graph.participants, type_participants)
    assert isinstance(graph.analysis, type_analysis)

    # TODO: Add assertions about incoming/outgoing attributes

    export = graph.to_dict()
    assert export == data_json

    graph.draw(Path("out"), "pdf")

    graph.to_nx()
