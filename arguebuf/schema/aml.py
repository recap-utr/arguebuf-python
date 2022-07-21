import xml.etree.ElementTree as et
from arguebuf.models.node import AtomNode, SchemeNode
from arguebuf.models.edge import Edge


def read_au(au: et.Element, g, nlp):
    # create the conclusion node
    prop = au.find("PROP")
    conclusion_node = AtomNode.from_aml(prop, nlp)
    if conclusion_node.id not in g.atom_nodes:
        g.add_node(conclusion_node)

    refutation = au.find("REFUTATION")
    if refutation is not None:
        # handle refutation
        # consider, that refutations are argument units (AU's)
        read_refutation(conclusion_node, g, refutation, nlp)

    # read premises and store in a list (list of et.Element objects)
    premises = [elem for elem in au if elem.tag == "CA" or elem.tag == "LA"]
    for elem in premises:
        if elem.tag == "CA":
            read_ca(conclusion_node, g, elem, nlp)
        elif elem.tag == "LA":
            read_la(conclusion_node, g, elem, nlp)

    # return graph
    return g


def read_refutation(conclusion: AtomNode, g, refutation: et.Element, nlp):
    # consists of one AU
    # get refutation
    au = refutation.find("AU")
    prop = au.find("PROP")
    premise_node = AtomNode.from_aml(prop, nlp)
    g.add_node(premise_node)

    # create SchemeNode (Attack)
    scheme_node = SchemeNode.from_aml(prop, nlp, refutation=True)
    g.add_node(scheme_node)

    # create edge from premise to schemeNode
    g.add_edge(Edge(premise_node, scheme_node))

    # create edge from schemeNode to conclusion
    g.add_edge(Edge(scheme_node, conclusion))

    # read the rest of au
    # read premises and store in a list (list of et.Element objects)
    premises = [elem for elem in au if elem.tag == "CA" or elem.tag == "LA"]
    for elem in premises:
        if elem.tag == "CA":
            read_ca(premise_node, g, elem, nlp)
        elif elem.tag == "LA":
            read_la(premise_node, g, elem, nlp)


def read_ca(conclusion: AtomNode, g, ca: et.Element, nlp):
    # first read premises
    for au in ca:
        # get premise
        prop = au.find("PROP")
        premise_node = AtomNode.from_aml(prop, nlp)
        g.add_node(premise_node)

        # create SchemeNode
        scheme_node = SchemeNode.from_aml(prop, nlp)
        g.add_node(scheme_node)

        # create edge from premise to schemeNode
        g.add_edge(Edge(premise_node, scheme_node))

        # create edge from schemeNode to conclusion
        g.add_edge(Edge(scheme_node, conclusion))

        # read the rest of au
        read_au(au, g, nlp)


def read_la(conclusion: AtomNode, g, la: et.Element, nlp):
    # first read premises
    for au in la:
        # get premise
        prop = au.find("PROP")
        premise_node = AtomNode.from_aml(prop, nlp)
        g.add_node(premise_node)

        # create SchemeNode
        scheme_node = SchemeNode.from_aml(prop, nlp)
        g.add_node(scheme_node)

        # create edge from premise to schemeNode
        g.add_edge(Edge(premise_node, scheme_node))

        # create edge from schemeNode to conclusion
        g.add_edge(Edge(scheme_node, conclusion))

        # read the rest of au
        read_au(au, g, nlp)
