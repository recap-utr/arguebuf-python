import re
from typing import TextIO

from arguebuf.model import Graph
from arguebuf.model.node import AtomNode
from arguebuf.model.scheme import Attack, Rephrase, Support

from ._config import Config

__all__ = ("load_kialo",)


def load_kialo[T = str](
    obj: TextIO,
    name: str | None = None,
    config: Config[T] = Config(),
) -> Graph[T]:
    """Generate Graph structure from a kialo discussion export."""
    if name_match := re.search(r"Discussion Title: (.*)", obj.readline()):
        name = name_match[1]

    if obj.readline().strip():
        raise ValueError("The title is not followed by an empty line!")

    g = config.graph(name)

    # Example: 1.1. Pro: Gold is better than silver.
    # Pattern: {ID}.{ID}. {STANCE (OPTIONAL)}: {TEXT}
    pattern = re.compile(r"^(1\.(?:\d+\.)+) (?:(Con|Pro): )?(.*)")
    current_line = obj.readline()
    next_line = obj.readline()

    mc_match = re.search(r"^((?:\d+\.)+) (.*)", current_line)

    if not mc_match:
        raise ValueError("The major claim is not present in the third line!")

    mc_id = mc_match[1]
    mc_text = mc_match[2]

    # See in the following while loop for explanation of this block
    while next_line and not pattern.search(next_line):
        mc_text = f"{mc_text}\n{next_line.strip()}"
        next_line = obj.readline()

    mc = _kialo_atom_node(mc_id, mc_text, config)
    g.add_node(mc)
    g.major_claim = mc

    current_line = next_line
    next_line = obj.readline()

    while current_line:
        if current_match := pattern.search(current_line):
            source_id = current_match[1]
            source_id_parts = source_id[:-1].split(".")
            stance = current_match[2]
            text = current_match[3]

            # The text of a node is allowed to span multiple lines.
            # Thus, we need to look ahead to concatenate the complete text.
            # As long as the pattern is not found in the next line,
            # we assume that the text belongs to the previous statement.
            while next_line and not pattern.search(next_line):
                text = f"{text}\n{next_line.strip()}"
                next_line = obj.readline()

            if id_ref_match := re.search(r"^-> See ((?:\d+\.)+)", text):
                id_ref = id_ref_match[1]
                source = g.atom_nodes[id_ref]
            else:
                source = _kialo_atom_node(source_id, text, config)
                g.add_node(source)

            match stance:
                case "Con":
                    scheme_type = Attack.DEFAULT
                case "Pro":
                    scheme_type = Support.DEFAULT
                case _:
                    scheme_type = Rephrase.DEFAULT

            scheme = config.SchemeNodeClass(scheme_type, id=f"{source_id}scheme")
            target_id = ".".join([*source_id_parts[:-1], ""])
            target = g.atom_nodes[target_id]
            g.add_edge(config.EdgeClass(source, scheme, id=f"{source.id}->{scheme.id}"))
            g.add_edge(config.EdgeClass(scheme, target, id=f"{scheme.id}->{target.id}"))

        # lines not matching the pattern would otherwise be processed forever
        current_line = next_line
        next_line = obj.readline()

    return g


def _kialo_atom_node[T](id: str, text: str, config: Config[T]) -> AtomNode[T]:
    # Remove backslashes before parentheses/brackets
    text = re.sub(r"\\([\[\]\(\)])", r"\1", text)

    # Remove markdown links
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)

    return config.AtomNodeClass(config.parse(text), id=id)
