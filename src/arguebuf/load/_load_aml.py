from typing import IO
from xml.etree import ElementTree as Tree

from arguebuf.model import Graph
from arguebuf.model.node import AtomNode, SchemeNode
from arguebuf.model.scheme import Attack, Support
from arguebuf.model.userdata import Userdata
from arguebuf.model.utils import uuid

from ._config import Config

__all__ = ("load_aml",)


def load_aml[T = str](
    obj: IO[str], name: str | None = None, config: Config[T] = Config()
) -> Graph[T]:
    """Generate Graph structure from AML argument graph file

    ElementTree XML API: https://docs.python.org/3/library/xml.etree.elementtree.html
    """
    root = Tree.parse(obj).getroot()
    g = config.graph(name)

    if (au := root.find("AU")) is not None:
        read_au(au, g, config)

    return g


def read_au[T](
    au: Tree.Element,
    g: Graph[T],
    config: Config[T],
    conclusion: AtomNode[T] | None = None,
) -> None:
    """Read an argument unit (AU) consisting of a conclusion and its premises."""
    if conclusion is None:
        if (prop := au.find("PROP")) is None:
            return

        conclusion = atom_from_aml(prop, config)
        g.add_node(conclusion)

    # refutations are argument units attacking the conclusion
    if (refutation := au.find("REFUTATION")) is not None and (
        refutation_au := refutation.find("AU")
    ) is not None:
        _read_premise(refutation_au, conclusion, g, config, refutation=True)

    # convergent (CA) and linked (LA) arguments contain premise units
    for elem in au:
        if elem.tag in ("CA", "LA"):
            for premise_au in elem:
                _read_premise(premise_au, conclusion, g, config, refutation=False)


def _read_premise[T](
    au: Tree.Element,
    conclusion: AtomNode[T],
    g: Graph[T],
    config: Config[T],
    refutation: bool,
) -> None:
    if (prop := au.find("PROP")) is None:
        return

    premise = atom_from_aml(prop, config)
    config.connect(g, premise, scheme_from_aml(prop, config, refutation), conclusion)
    read_au(au, g, config, premise)


def _owners(obj: Tree.Element) -> Userdata:
    if owners := [owner.get("name") or "" for owner in obj.findall("OWNER")]:
        return {"owners": ", ".join(owners)}

    return {}


def atom_from_aml[T](obj: Tree.Element, config: Config[T]) -> AtomNode[T]:
    """Generate an atom node from an AML "PROP" element."""
    text_element = obj.find("PROPTEXT")

    return config.AtomNodeClass(
        config.parse(text_element.text if text_element is not None else None),
        userdata=_owners(obj),
        id=obj.get("identifier") or uuid(),
    )


def scheme_from_aml[T](
    obj: Tree.Element, config: Config[T], refutation: bool = False
) -> SchemeNode:
    """Generate a scheme node from an AML "PROP" element."""
    scheme: Support | Attack = Support.DEFAULT

    if refutation:
        scheme = Attack.DEFAULT
    elif (inscheme := obj.find("INSCHEME")) is not None:
        aml_scheme = inscheme.attrib["scheme"].lower().replace(" ", "")
        scheme = next(
            (
                support
                for support in Support
                if support.value.lower().replace(" ", "") in aml_scheme
            ),
            Support.DEFAULT,
        )

    # the scheme is derived from the premise and thus needs a distinct id
    identifier = obj.get("identifier")

    return config.SchemeNodeClass(
        scheme,
        userdata=_owners(obj),
        id=f"{identifier}scheme" if identifier else uuid(),
    )
