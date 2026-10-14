import csv
from typing import TextIO

from arguebuf.model import Graph
from arguebuf.model.node import AtomNode
from arguebuf.model.scheme import Attack, Support

from ._config import Config

__all__ = ("load_brat",)


def load_brat[T = str](
    obj: TextIO,
    name: str | None = None,
    config: Config[T] = Config(),
) -> Graph[T]:
    """Generate Graph structure from BRAT argument graph file (reference: https://brat.nlplab.org/)"""
    g = config.graph(name)
    atom_nodes: dict[str, AtomNode[T]] = {}
    major_claim_texts: list[str] = []
    mc = config.AtomNodeClass(config.parse(""))
    g.add_node(mc)
    g.major_claim = mc

    for row in csv.reader(obj, delimiter="\t"):
        annotation = row[1].split()

        if row[0].startswith("T"):
            if annotation[0] == "MajorClaim":
                major_claim_texts.append(row[2])
            else:
                atom = config.AtomNodeClass(config.parse(row[2]))
                g.add_node(atom)
                atom_nodes[row[0]] = atom

        elif row[0].startswith("A"):
            scheme = Attack.DEFAULT if annotation[2] == "Against" else Support.DEFAULT
            config.connect(
                g, atom_nodes[annotation[1]], config.SchemeNodeClass(scheme), mc
            )

        elif row[0].startswith("R"):
            scheme = Attack.DEFAULT if annotation[0] == "attacks" else Support.DEFAULT
            source = atom_nodes[annotation[1].split(":")[1]]
            target = atom_nodes[annotation[2].split(":")[1]]
            config.connect(g, source, config.SchemeNodeClass(scheme), target)

    # multiple major claims of an essay are merged into a single node
    mc.text = config.parse(". ".join(major_claim_texts))

    return g
