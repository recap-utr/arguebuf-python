from __future__ import absolute_import, annotations

from dataclasses import dataclass, field
from typing import Union

from spacy.language import Language
from spacy.tokens import Doc, Span

from . import utils


# TODO: Implement annotated text


@dataclass
class Analysis:
    """Needed to store metadata for OVA."""

    text: Union[str, Doc, Span] = None
    annotator_name: str = ""
    document_source: str = ""
    document_title: str = ""

    @property
    def annotated_text(self):
        return self.text

    @staticmethod
    def from_ova(obj: Any, nlp: Optional[Language] = None) -> Analysis:
        return Analysis(
            text=utils.parse(obj.get("plain_txt"), nlp),
            annotator_name=obj.get("annotatorName"),
            document_source=obj.get("documentSource"),
            document_title=obj.get("documentTitle"),
        )

    def to_ova(self) -> dict:
        return {
            "txt": self.annotated_text or "",
            "plain_txt": self.text or "",
            "annotatorName": self.annotator_name,
            "documentSource": self.document_source,
            "documentTitle": self.document_title,
        }
