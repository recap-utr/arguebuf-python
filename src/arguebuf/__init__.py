"""
.. include:: ../../README.md
"""

import logging

from . import dump, load, model, render, schemas, traverse
from .model import (
    AbstractNode,
    Analyst,
    AtomNode,
    AtomOrSchemeNode,
    Attack,
    Edge,
    Graph,
    Metadata,
    Participant,
    Preference,
    Reference,
    Rephrase,
    Resource,
    Scheme,
    SchemeNode,
    Support,
    Userdata,
    uuid,
)
from .utils import copy

logging.getLogger(__name__).addHandler(logging.NullHandler())

__all__ = (
    "AbstractNode",
    "Analyst",
    "AtomNode",
    "AtomOrSchemeNode",
    "Attack",
    "Edge",
    "Graph",
    "Metadata",
    "Participant",
    "Preference",
    "Reference",
    "Rephrase",
    "Resource",
    "Scheme",
    "SchemeNode",
    "Support",
    "Userdata",
    "copy",
    "dump",
    "load",
    "model",
    "render",
    "schemas",
    "traverse",
    "uuid",
)
