from pathlib import Path

import arguebuf as ag


def test_render_graph(tmp_path: Path):
    # Create test graph
    g = ag.Graph("Test")

    # Create atom nodes
    an1 = ag.AtomNode(text="Lincoln Chafee just isn't presidential material")
    an2 = ag.AtomNode(text="Chafee is president material")
    an3 = ag.AtomNode(
        text=(
            "if elections weren't just popularity contests Chafee would probably do"
            " just fine"
        )
    )
    an4 = ag.AtomNode(text="Chafee is just not figurehead material")
    an5 = ag.AtomNode(text="Chafee does have good positions")
    an6 = ag.AtomNode(text="chafee seems more like a cool college professor")
    an7 = ag.AtomNode(text="I was speaking more of Chafee's presentation")
    an8 = ag.AtomNode(text="Chafee is very charismatic")

    # Create scheme nodes
    sn1 = ag.SchemeNode(scheme=ag.Attack.DEFAULT)
    sn2 = ag.SchemeNode(scheme=ag.Support.DEFAULT)
    sn3 = ag.SchemeNode(scheme=ag.Support.DEFAULT)
    sn4 = ag.SchemeNode(scheme=ag.Support.DEFAULT)
    sn5 = ag.SchemeNode(scheme=ag.Support.DEFAULT)
    sn6 = ag.SchemeNode(scheme=ag.Rephrase.DEFAULT)
    sn7 = ag.SchemeNode(scheme=ag.Attack.DEFAULT)

    # Create edges
    e1 = ag.Edge(an3, sn2)
    e2 = ag.Edge(sn2, an2)
    e3 = ag.Edge(an2, sn1)
    e4 = ag.Edge(sn1, an1)
    e5 = ag.Edge(sn3, an3)
    e6 = ag.Edge(an4, sn3)
    e7 = ag.Edge(sn4, an3)
    e8 = ag.Edge(an5, sn4)
    e9 = ag.Edge(sn5, an1)
    e10 = ag.Edge(an6, sn5)
    e11 = ag.Edge(sn6, an6)
    e12 = ag.Edge(an7, sn6)
    e13 = ag.Edge(sn7, an6)
    e14 = ag.Edge(an8, sn7)

    # Add edges to graph g
    g.add_edge(e1)
    g.add_edge(e2)
    g.add_edge(e3)
    g.add_edge(e4)
    g.add_edge(e5)
    g.add_edge(e6)
    g.add_edge(e7)
    g.add_edge(e8)
    g.add_edge(e9)
    g.add_edge(e10)
    g.add_edge(e11)
    g.add_edge(e12)
    g.add_edge(e13)
    g.add_edge(e14)

    # Dump graph into d2 graph and graphviz graph
    d2_graph = ag.dump.d2(g)
    graphviz_graph = ag.dump.graphviz(g)

    # Render d2 graph and graphviz graph
    if d2_graph is not None:
        ag.render.d2(d2_graph, tmp_path / "test_d2.png")

    if graphviz_graph is not None:
        ag.render.graphviz(graphviz_graph, tmp_path / "test_graphviz.png")
