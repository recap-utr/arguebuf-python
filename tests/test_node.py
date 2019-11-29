import pytest
import json
import argument_graph as ag
import spacy


@pytest.fixture
def node_json():
    return json.loads(
        """
{
    "nodeID": "119935",
    "text": "One can hardly move in Friedrichshain or Neuk\u00f6lln these days without permanently scanning the ground for dog dirt.",
    "type": "I",
    "timestamp": "2015-12-14 12:09:15"
}
"""
    )


@pytest.fixture
def nlp():
    return spacy.load("en")


def test_node(node_json, nlp):
    node = ag.Node.from_aif(node_json, nlp)
