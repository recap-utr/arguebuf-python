from typing import IO
from xml.etree import ElementTree as Tree

from arguebuf.model import Graph
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.scheme import Attack, Scheme, Support, resolve_scheme
from arguebuf.model.userdata import DEFAULT_CODECS, Codec, Codecs, JsonObject
from arguebuf.model.utils import uuid

from ._helpers import connect

__all__ = ("load_aml",)


def load_aml[
    A = JsonObject,
    S = JsonObject,
    E = JsonObject,
    G = JsonObject,
    R = JsonObject,
    P = JsonObject,
    N = JsonObject,
](
    obj: IO[str],
    name: str | None = None,
    *,
    codecs: Codecs[A, S, E, G, R, P, N] = DEFAULT_CODECS,
) -> Graph[A, S, E, G, R, P, N]:
    """Generate Graph structure from AML argument graph file

    The proposition (PROP) of the top argument unit (AU) is the major claim.
    The premise units of a linked argument (LA) share one scheme node,
    those of a convergent argument (CA) and refutations get one each.
    A scheme is derived from the first premise PROP of its group (see `scheme_from_aml`).

    ElementTree XML API: https://docs.python.org/3/library/xml.etree.elementtree.html
    """
    root = Tree.parse(obj).getroot()
    g: Graph[A, S, E, G, R, P, N] = Graph(
        name, userdata=codecs.graph.validate_python({})
    )

    if (au := root.find("AU")) is not None and (prop := au.find("PROP")) is not None:
        major_claim = atom_from_aml(prop, codecs.atom)
        g.add_node(major_claim)
        g.major_claim = major_claim
        read_au(au, g, codecs, major_claim)

    return g


def read_au[A, S, E, G, R, P, N](
    au: Tree.Element,
    g: Graph[A, S, E, G, R, P, N],
    codecs: Codecs[A, S, E, G, R, P, N],
    conclusion: AtomNode[A],
) -> None:
    """Read the premises of an argument unit (AU) whose PROP is the `conclusion`."""
    # a refutation is an argument unit attacking the conclusion
    if (refutation := au.find("REFUTATION/AU")) is not None:
        _read_premises([refutation], conclusion, g, codecs, refutation=True)

    for elem in au:
        if elem.tag == "LA":
            _read_premises(list(elem), conclusion, g, codecs, refutation=False)
        elif elem.tag == "CA":
            for premise_au in elem:
                _read_premises([premise_au], conclusion, g, codecs, refutation=False)


def _read_premises[A, S, E, G, R, P, N](
    aus: list[Tree.Element],
    conclusion: AtomNode[A],
    g: Graph[A, S, E, G, R, P, N],
    codecs: Codecs[A, S, E, G, R, P, N],
    refutation: bool,
) -> None:
    units = [(au, prop) for au in aus if (prop := au.find("PROP")) is not None]

    if not units:
        return

    premises = [atom_from_aml(prop, codecs.atom) for _, prop in units]

    for premise in premises:
        g.add_node(premise)

    scheme = scheme_from_aml(units[0][1], codecs.scheme, refutation)
    g.add_node(scheme)
    connect(g, codecs, [premise.id for premise in premises], scheme.id, conclusion.id)

    for (au, _), premise in zip(units, premises, strict=True):
        read_au(au, g, codecs, premise)


def _owners(obj: Tree.Element) -> JsonObject:
    if owners := [owner.get("name") or "" for owner in obj.findall("OWNER")]:
        return {"owners": ", ".join(owners)}

    return {}


def atom_from_aml[A](obj: Tree.Element, codec: Codec[A]) -> AtomNode[A]:
    """Generate an atom node from an AML "PROP" element."""
    return AtomNode(
        obj.findtext("PROPTEXT", ""),
        userdata=codec.validate_python(_owners(obj)),
        id=obj.get("identifier") or uuid(),
    )


def scheme_from_aml[S](
    obj: Tree.Element, codec: Codec[S], refutation: bool = False
) -> SchemeNode[S]:
    """Generate a scheme node from an AML "PROP" element."""
    scheme: Scheme = Support.DEFAULT

    if refutation:
        scheme = Attack.DEFAULT
    elif (inscheme := obj.find("INSCHEME")) is not None:
        scheme = resolve_scheme(Support, inscheme.attrib["scheme"])

    # the scheme is derived from the premise and thus needs a distinct id
    identifier = obj.get("identifier")

    return SchemeNode(
        scheme,
        userdata=codec.validate_python(_owners(obj)),
        id=f"{identifier}scheme" if identifier else uuid(),
    )
