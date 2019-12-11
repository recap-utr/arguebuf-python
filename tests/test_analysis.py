import pytest
import pendulum
import json
import recap_argument_graph as ag


data = [
    (
        """
        {
            "ovaVersion": "1.2.0",
            "txt": "<span class=\\"highlighted\\" id=\\"node119935\\">One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt.</span> <span class=\\"highlighted\\" id=\\"node119936\\">And when bad luck does strike and you step into one of the many 'land mines' you have to painstakingly scrape the remains off your soles.</span> <span class=\\"highlighted\\" id=\\"node119937\\">Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners.</span> <span class=\\"highlighted\\" id=\\"node119938\\">Of course, first they'd actually need to be caught in the act by public order officers,</span> <span class=\\"highlighted\\" id=\\"node119939\\">but once they have to dig into their pockets, their laziness will sure vanish!</span><br>",
            "plain_txt": "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt. And when bad luck does strike and you step into one of the many 'land mines' you have to painstakingly scrape the remains off your soles. Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners. Of course, first they'd actually need to be caught in the act by public order officers, but once they have to dig into their pockets, their laziness will sure vanish!\\n",
            "annotatorName": "Anna Ludwig",
            "documentTitle": "nodeset6362.json",
            "documentDate": "30/11/2019"
        }
        """,
        "1.2.0",
        "One can hardly move in Friedrichshain or Neukölln these days without permanently scanning the ground for dog dirt. And when bad luck does strike and you step into one of the many 'land mines' you have to painstakingly scrape the remains off your soles. Higher fines are therefore the right measure against negligent, lazy or simply thoughtless dog owners. Of course, first they'd actually need to be caught in the act by public order officers, but once they have to dig into their pockets, their laziness will sure vanish!\n",
        "Anna Ludwig",
        "nodeset6362.json",
        None,
        pendulum.datetime(2019, 11, 30),
    )
]


@pytest.mark.parametrize(
    "data,ova_version,text,annotator_name,document_title,document_source,document_date",
    data,
)
def test_analysis(
    data,
    ova_version,
    text,
    annotator_name,
    document_title,
    document_source,
    document_date,
):
    data_json = json.loads(data)
    analysis = ag.Analysis.from_ova(data_json)

    assert analysis.ova_version == ova_version
    assert analysis.text == text
    assert bool(analysis.annotated_text)
    assert analysis.annotator_name == annotator_name
    assert analysis.document_title == document_title
    assert analysis.document_source == document_source
    assert analysis.document_date == document_date

    export = analysis.to_ova()
    assert export.items() >= data_json.items()
