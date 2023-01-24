import typing as t
import xml.etree.ElementTree as ET

import pendulum

from arguebuf.converters.config import ConverterConfig, DefaultConverter
from arguebuf.models.edge import Edge
from arguebuf.models.graph import Graph
from arguebuf.models.metadata import Metadata
from arguebuf.models.node import AtomNode, Attack, SchemeNode, Support
from arguebuf.services import utils


def from_aml(
    obj: t.IO, name: t.Optional[str] = None, config: ConverterConfig = DefaultConverter
) -> Graph:
    """
    Generate Graph structure from AML argument graph file
    ElementTree XML API: https://docs.python.org/3/library/xml.etree.elementtree.html#
    """

    tree = ET.parse(obj)
    root = tree.getroot()

    # create nodes and edges from AU element
    au = root.find("AU")
    g = config.GraphClass(name)
    assert isinstance(au, ET.Element)
    g = read_au(au, g, config)

    # create edge objects and add to g

    # create Metadata object
    # create Analyst object
    # create Userdata

    return g


def read_au(au: ET.Element, g: Graph, config: ConverterConfig):
    # create the conclusion node
    prop = au.find("PROP")
    if prop is not None:
        conclusion_node = atom_from_aml(prop, config)
        if conclusion_node.id not in g.atom_nodes:
            g.add_node(conclusion_node)

        refutation = au.find("REFUTATION")
        if refutation is not None:
            # handle refutation
            # consider, that refutations are argument units (AU's)
            read_refutation(conclusion_node, g, refutation, config)

        # read premises and store in a list (list of ET.Element objects)
        premises = [elem for elem in au if elem.tag == "CA" or elem.tag == "LA"]
        for elem in premises:
            if elem.tag == "CA":
                read_ca(conclusion_node, g, elem, config)
            elif elem.tag == "LA":
                read_la(conclusion_node, g, elem, config)

    # return graph
    return g


def read_refutation(
    conclusion: AtomNode, g, refutation: ET.Element, config: ConverterConfig
):
    # consists of one AU
    # get refutation
    au = refutation.find("AU")

    if au is not None:
        prop = au.find("PROP")

        if prop is not None:
            premise_node = atom_from_aml(prop, config)
            g.add_node(premise_node)

            # create SchemeNode (Attack)
            scheme_node = scheme_from_aml(prop, config, refutation=True)
            g.add_node(scheme_node)

            # create edge from premise to schemeNode
            g.add_edge(Edge(premise_node, scheme_node))

            # create edge from schemeNode to conclusion
            g.add_edge(Edge(scheme_node, conclusion))

            # read the rest of au
            # read premises and store in a list (list of ET.Element objects)
            premises = [elem for elem in au if elem.tag == "CA" or elem.tag == "LA"]
            for elem in premises:
                if elem.tag == "CA":
                    read_ca(premise_node, g, elem, config)
                elif elem.tag == "LA":
                    read_la(premise_node, g, elem, config)


def read_ca(conclusion: AtomNode, g: Graph, ca: ET.Element, config: ConverterConfig):
    # first read premises
    for au in ca:
        # get premise
        prop = au.find("PROP")

        if prop is not None:
            premise_node = atom_from_aml(prop, config)
            g.add_node(premise_node)

            # create SchemeNode
            scheme_node = scheme_from_aml(prop, config)
            g.add_node(scheme_node)

            # create edge from premise to schemeNode
            g.add_edge(config.EdgeClass(premise_node, scheme_node))

            # create edge from schemeNode to conclusion
            g.add_edge(config.EdgeClass(scheme_node, conclusion))

            # read the rest of au
            read_au(au, g, config)


def read_la(conclusion: AtomNode, g: Graph, la: ET.Element, config: ConverterConfig):
    # first read premises
    for au in la:
        # get premise
        prop = au.find("PROP")

        if prop is not None:
            premise_node = atom_from_aml(prop, config)
            g.add_node(premise_node)

            # create SchemeNode
            scheme_node = scheme_from_aml(prop, config)
            g.add_node(scheme_node)

            # create edge from premise to schemeNode
            g.add_edge(Edge(premise_node, scheme_node))

            # create edge from schemeNode to conclusion
            g.add_edge(Edge(scheme_node, conclusion))

            # read the rest of au
            read_au(au, g, config)


def atom_from_aml(
    obj: ET.Element,
    config: ConverterConfig,
) -> AtomNode:
    """
    Generate Node object from AML Node format. obj is a AML "PROP" element.
    """
    # get id of PROP
    id = obj.get("identifier")

    # read text of PROP
    text = None
    text_element = obj.find("PROPTEXT")

    if text_element is not None:
        text = text_element.text

    # read owners of PROP
    owner_list = obj.findall("OWNER")
    owners_lst = []
    if not owner_list:
        # if not empty, do something
        for owner in owner_list:
            owners_lst.append(owner.get("name"))
        owners = {"owners": ", ".join(owners_lst)}
    else:
        owners = {}

    # create timestamp
    timestamp = pendulum.now()

    return config.AtomNodeClass(
        id=id,
        text=utils.parse(text, config.nlp),
        metadata=Metadata(timestamp, timestamp),
        userdata=owners,
    )


def scheme_from_aml(
    obj: ET.Element,
    config: ConverterConfig,
    refutation=False,
) -> SchemeNode:
    """Generate SchemeNode object from AML Node format. obj is a AML "PROP" element."""

    # get id of PROP
    if "identifier" in obj.attrib:
        id = obj.get("identifier")
    else:
        id = None

    # read owners of PROP
    owner_list = obj.findall("OWNER")
    owners_lst = []
    if not owner_list:
        # if not empty, do something
        for owner in owner_list:
            owners_lst.append(owner.get("name"))
        owners = {"owners": ", ".join(owners_lst)}
    else:
        owners = {}

    # create timestamp
    timestamp = pendulum.now()

    # get scheme name
    scheme = None
    if refutation:
        scheme = Attack.DEFAULT
    else:
        inscheme = obj.find("INSCHEME")
        if inscheme is not None:  # if INSCHEME element is available
            # get scheme
            aml_scheme = inscheme.attrib["scheme"]
            contains_scheme = False
            for supp_scheme in Support:
                if supp_scheme.value.lower().replace(
                    " ", ""
                ) in aml_scheme.lower().replace(" ", ""):
                    scheme = supp_scheme
                    contains_scheme = True
                    break
            if not contains_scheme:
                scheme = Support.DEFAULT
        else:  # if INSCHEME element is not available
            scheme = Support.DEFAULT

    return config.SchemeNodeClass(
        metadata=Metadata(timestamp, timestamp),
        scheme=scheme,
        userdata=owners,
        id=id,
    )
