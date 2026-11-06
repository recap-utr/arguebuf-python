from datetime import UTC, datetime
from xml.etree import ElementTree as ET

import arguebuf as ag
from arguebuf.load._helpers import Context
from arguebuf.load._load_aif import node_from_aif
from arguebuf.load._load_aml import atom_from_aml, scheme_from_aml
from arguebuf.load._load_sadface import atom_from_sadface, scheme_from_sadface
from arguebuf.model.userdata import JSON_CODEC, Codecs
from arguebuf.schemas import aif, sadface


def test_aml_atom() -> None:
    tree = ET.fromstring(
        '<PROP identifier="B"><PROPTEXT>Premise</PROPTEXT><OWNER name="Alice" /></PROP>'
    )
    node = atom_from_aml(tree, JSON_CODEC)

    assert node.id == "B"
    assert node.text == "Premise"
    assert node.reference is None
    assert node.userdata == {"owners": "Alice"}


def test_sadface_atom() -> None:
    node = atom_from_sadface(
        sadface.Node(id="a", text="Claim", type="atom"),
        {},
        Context(Codecs()),
        JSON_CODEC,
    )

    assert node.id == "a"
    assert node.text == "Claim"
    assert node.reference is None
    assert node.userdata == {}


def test_aif_atom() -> None:
    node = node_from_aif(
        aif.Node(nodeID="a", text="Claim", type="I", timestamp="2015-12-14 12:09:15"),
        JSON_CODEC,
        JSON_CODEC,
    )

    assert isinstance(node, ag.AtomNode)
    assert node.id == "a"
    assert node.text == "Claim"
    assert (
        node.metadata.created
        == node.metadata.updated
        == datetime(2015, 12, 14, 12, 9, 15, tzinfo=UTC)
    )
    assert node.reference is None
    assert node.userdata == {}


def test_sadface_scheme() -> None:
    node = scheme_from_sadface(
        sadface.Node(id="s", name="support", type="scheme"), JSON_CODEC
    )

    assert node.id == "s"
    assert node.scheme == ag.Support.DEFAULT


def test_aif_scheme() -> None:
    node = node_from_aif(
        aif.Node(nodeID="s", text="Default Inference", type="RA"),
        JSON_CODEC,
        JSON_CODEC,
    )

    assert isinstance(node, ag.SchemeNode)
    assert node.id == "s"
    assert node.scheme == ag.Support.DEFAULT


def test_aml_scheme() -> None:
    tree = ET.fromstring(
        '<PROP identifier="A"><INSCHEME scheme=" Argument From Sign " /></PROP>'
    )
    node = scheme_from_aml(tree, JSON_CODEC)

    assert node.id == "Ascheme"
    assert node.scheme == ag.Support.SIGN
