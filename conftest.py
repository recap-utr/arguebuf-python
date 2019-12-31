import pytest
import recap_argument_graph as ag


@pytest.fixture()
def init_graph():
    return ag.Graph("Test")
