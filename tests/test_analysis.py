import pytest
import json
import argument_graph as ag


data = [
    (
        """
        {
            "txt": "<span class=\\"highlighted\\" id=\\"node119935\\">One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.</span> <span class=\\"highlighted\\" id=\\"node119936\\">And when bad luck does strike and you step into one of the many 'land mines' you have to painstakingly scrape the remains off your soles.</span> <span class=\\"highlighted\\" id=\\"node119937\\">Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners.</span> <span class=\\"highlighted\\" id=\\"node119938\\">Of course, first they'd actually need to be caught in the act by public order officers,</span> <span class=\\"highlighted\\" id=\\"node119939\\">but once they have to dig into their pockets, their laziness will sure vanish!</span><br>",
            "plain_txt": "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt. And when bad luck does strike and you step into one of the many 'land mines' you have to painstakingly scrape the remains off your soles. Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners. Of course, first they'd actually need to be caught in the act by public order officers, but once they have to dig into their pockets, their laziness will sure vanish!\\n",
            "annotatorName": "Anna Ludwig",
            "documentTitle": "nodeset6362.json"
        }
        """,
        "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt. And when bad luck does strike and you step into one of the many 'land mines' you have to painstakingly scrape the remains off your soles. Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners. Of course, first they'd actually need to be caught in the act by public order officers, but once they have to dig into their pockets, their laziness will sure vanish!\n",
        "Anna Ludwig",
        "nodeset6362.json",
    )
]


@pytest.mark.parametrize("data,text,annotator,title", data)
def test_analysis(data, text, annotator, title):
    analysis = ag.Analysis.from_ova(json.loads(data))

    assert analysis.text == text
    assert bool(analysis.annotated_text)
    assert analysis.annotator_name == annotator
    assert analysis.document_title == title
