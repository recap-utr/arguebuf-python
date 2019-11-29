from __future__ import absolute_import, annotations

import uuid
from spacy.language import Language


def unique_id() -> int:
    return uuid.uuid1().int >> 64


def xstr(data: Any):
    return "" if data is None else str(data)


def parse(text: str, nlp: Optional[Language]):
    return nlp(text) if nlp else text
