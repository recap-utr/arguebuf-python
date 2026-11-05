import dataclasses
import re
from dataclasses import dataclass
from typing import TextIO

from arguebuf.model import Graph, GraphDraft
from arguebuf.model.issue import Reporter
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.scheme import Attack, Rephrase, Scheme, Support
from arguebuf.model.userdata import DEFAULT_CODECS, Codecs, JsonObject

from ._helpers import Context, connect, lookup

__all__ = ("load_kialo",)

title_pattern = re.compile(r"Discussion Title: (.*)")
# Example: 1.1. Pro: Gold is better than silver.
# Pattern: {ID}.{ID}. {STANCE (OPTIONAL)}: {TEXT}
_statement = re.compile(r"^(1\.(?:\d+\.)*) (?:(Con|Pro): )?(.*)")
_reference = re.compile(r"^-> See ((?:\d+\.)+)")
# link targets may contain one level of parentheses, e.g. Wikipedia URLs
_link = re.compile(r"\[([^\]]*)\]\((?:[^()]|\([^()]*\))*\)")
_escape = re.compile(r"\\([\[\]\(\)])")
stance2scheme: dict[str | None, Scheme] = {
    "Pro": Support.DEFAULT,
    "Con": Attack.DEFAULT,
    None: Rephrase.DEFAULT,
}


@dataclass(slots=True, frozen=True)
class _Statement:
    stance: str | None
    text: str


def load_kialo[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
    G = JsonObject,
](
    obj: TextIO,
    name: str | None = None,
    *,
    codecs: Codecs[A, S, E, R, P, N, G] = DEFAULT_CODECS,
    on_issue: Reporter | None = None,
    strict: bool = False,
) -> Graph[A, S, E, R, P, N, G]:
    """Generate Graph structure from a kialo discussion export.

    The discussion title becomes the name of the graph (overriding `name`)
    and the first statement its major claim.
    Statements use their kialo id (e.g. `1.2.`) as atom id and span all lines until the next statement.
    A statement `-> See 1.3.` refers to the atom of another statement,
    so it and its children are attached to that atom.
    Markdown links are replaced by their text and escaped brackets are unescaped.
    """
    if name_match := title_pattern.search(obj.readline()):
        name = name_match[1].strip()

    if obj.readline().strip():
        raise ValueError("The title is not followed by an empty line!")

    statements: dict[str, _Statement] = {}
    # id of the statement that following lines continue
    current: str | None = None

    for line in obj:
        match = _statement.search(line)

        # only the major claim has the id `1.`, all others are nested below it
        if not statements:
            if not match or match[1] != "1.":
                raise ValueError("The major claim is not present in the third line!")

            statements[match[1]] = _Statement(None, match[3])
            current = match[1]
        elif match and match[1] != "1.":
            if match[1] in statements:
                raise ValueError(f"The statement '{match[1]}' is not unique!")

            statements[match[1]] = _Statement(match[2], match[3])
            current = match[1]
        elif current:
            statement = statements[current]
            statements[current] = dataclasses.replace(
                statement, text=f"{statement.text}\n{line.strip()}"
            )

    if not statements:
        raise ValueError("The major claim is not present in the third line!")

    ctx = Context(codecs, on_issue, strict)
    g: GraphDraft[A, S, E, R, P, N, G] = GraphDraft(
        name, userdata=codecs.graph.validate_python({})
    )
    references: dict[str, str] = {}

    for id, statement in statements.items():
        text = statement.text.strip()

        if reference := _reference.search(text):
            references[id] = reference[1]
        else:
            g.add_node(
                AtomNode(
                    _escape.sub(r"\1", _link.sub(r"\1", text)),
                    userdata=codecs.atom.validate_python({}),
                    id=id,
                )
            )

    atoms = g.atom_nodes

    def resolve(id: str, owner: str) -> AtomNode[A] | None:
        visited: set[str] = set()

        while id in references and id not in visited:
            visited.add(id)
            id = references[id]

        return lookup(ctx, atoms, id, "statement", owner)

    g.major_claim = resolve("1.", "the major claim")

    for id, statement in list(statements.items())[1:]:
        parent_id = id[: id.rindex(".", 0, -1) + 1]
        owner = f"statement '{id}'"

        if (source := resolve(id, owner)) and (target := resolve(parent_id, owner)):
            scheme = SchemeNode(
                stance2scheme[statement.stance],
                userdata=codecs.scheme.validate_python({}),
                id=f"{id}scheme",
            )
            g.add_node(scheme)
            connect(g, ctx, [source.id], scheme.id, target.id)

    return g.freeze()
