from collections.abc import Iterable
from typing import TextIO

from arguebuf.model import Graph
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.scheme import Attack, Rephrase, Scheme, Support
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject

from ._helpers import connect, log, lookup

__all__ = ("load_brat",)

relation2scheme: dict[str, Scheme] = {
    "supports": Support.DEFAULT,
    "attacks": Attack.DEFAULT,
}
stance2scheme: dict[str, Scheme] = {
    "For": Support.DEFAULT,
    "Against": Attack.DEFAULT,
}


def load_brat[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
](
    obj: TextIO,
    name: str | None = None,
    *,
    codecs: Codecs[A, S, E, G, R, P, N] = DEFAULT_CODECS,
) -> Graph[A, S, E, G, R, P, N]:
    """Generate Graph structure from BRAT argument graph file (reference: https://brat.nlplab.org/).

    Lines consist of tab-separated columns, blank lines are skipped.
    Text-bound annotations (`T1 Claim 0 10 text`) become atoms with the brat id.
    The first `MajorClaim` is the major claim, further ones rephrase it.
    Stances (`A1 Stance T2 For|Against`) support or attack the major claim,
    relations (`R1 supports|attacks Arg1:T3 Arg2:T2`) connect their arguments by role.
    Scheme nodes use the id of their annotation (`<T id>scheme` for rephrases).
    Unknown stances, relation types, and atoms are skipped with a warning,
    lines of other shapes are ignored.
    """
    g: Graph[A, S, E, G, R, P, N] = Graph(
        name, userdata=codecs.graph.validate_python({})
    )
    rows = [line.rstrip("\r\n").split("\t") for line in obj if line.strip()]

    for row in rows:
        match row:
            case [id, annotation, text, *_] if id.startswith("T"):
                atom = AtomNode(text, userdata=codecs.atom.validate_python({}), id=id)
                g.add_node(atom)

                if annotation.split()[:1] == ["MajorClaim"]:
                    if g.major_claim is None:
                        g.major_claim = atom
                    else:
                        g.add_node(
                            SchemeNode(
                                Rephrase.DEFAULT,
                                userdata=codecs.scheme.validate_python({}),
                                id=f"{id}scheme",
                            )
                        )
                        connect(g, codecs, [id], f"{id}scheme", g.major_claim.id)

    atoms = g.atom_nodes

    for row in rows:
        if len(row) < 2:
            continue

        id, annotation = row[0], row[1].split()
        owner = f"annotation '{id}'"

        match id[:1], annotation:
            case "A", ["Stance", source_id, stance]:
                scheme = lookup(stance2scheme, stance, "stance", owner)
                source = lookup(atoms, source_id, "atom", owner)
                target = g.major_claim

                if target is None:
                    log.warning("Skipping stance '%s' without a major claim.", id)

            case "R", [relation, *arguments] if {"Arg1", "Arg2"} <= (
                roles := _roles(arguments)
            ).keys():
                scheme = lookup(relation2scheme, relation, "relation type", owner)
                source = lookup(atoms, roles["Arg1"], "atom", owner)
                target = lookup(atoms, roles["Arg2"], "atom", owner)

            case _:
                continue

        if scheme and source and target:
            g.add_node(
                SchemeNode(scheme, userdata=codecs.scheme.validate_python({}), id=id)
            )
            connect(g, codecs, [source.id], id, target.id)

    return g


def _roles(arguments: Iterable[str]) -> dict[str, str]:
    """Map the roles of relation arguments like `Arg1:T3` to their ids."""
    return {
        role: value
        for role, separator, value in (
            argument.partition(":") for argument in arguments
        )
        if separator
    }
