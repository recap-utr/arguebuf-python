import pytest

import arguebuf as ag


@pytest.fixture()
def init_graph():
    return ag.Graph("Test")
