import csv
import typing as t

from arguebuf.model import Graph, utils
from arguebuf.model.scheme import Attack, Support

from ._config import Config, DefaultConfig

__all__ = ("load_brat",)


def load_brat(
    obj: t.TextIO,
    name: t.Optional[str] = None,
    config: Config = DefaultConfig,
) -> Graph:
    """Generate Graph structure from BRAT argument graph file (reference: https://brat.nlplab.org/)"""
    reader = csv.reader(obj, delimiter="\t")
    g = config.GraphClass(name)

    atom_nodes = {}
    mc = config.AtomNodeClass(utils.parse("", config.nlp))
    g.add_node(mc)
    g._major_claim = mc

    for row in reader:
        userdata = row[1].split()

        if row[0].startswith("T"):
            if userdata[0] == "MajorClaim":
                mc.text = utils.parse(f"{mc.plain_text}. {row[2]}", config.nlp)
            else:
                atom = config.AtomNodeClass(utils.parse(row[2], config.nlp))
                g.add_node(atom)
                atom_nodes[row[0]] = atom

        elif row[0].startswith("A") or row[0].startswith("R"):
            if row[0].startswith("A"):
                scheme_type = (
                    Attack.DEFAULT if userdata[2] == "Against" else Support.DEFAULT
                )
                source = atom_nodes[userdata[1]]
                target = mc
            else:
                scheme_type = (
                    Attack.DEFAULT if userdata[0] == "attacks" else Support.DEFAULT
                )
                source = atom_nodes[userdata[1].split(":")[1]]
                target = atom_nodes[userdata[2].split(":")[1]]

            scheme = config.SchemeNodeClass(scheme_type)
            g.add_node(scheme)

            g.add_edge(config.EdgeClass(source, scheme))
            g.add_edge(config.EdgeClass(scheme, target))

    return g
