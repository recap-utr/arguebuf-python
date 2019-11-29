from __future__ import absolute_import, annotations

from dataclasses import dataclass, field

from spacy.language import Language
from spacy.tokens import Doc


@dataclass
class Analysis:
    """Needed to store metadata for OVA."""

    nlp: Language
    _text: Doc = None
    annotator_name: str = ""
    document_source: str = ""
    document_title: str = ""

    @property
    def annotated_text(self):
        return self.text

    @property
    def text(self) -> Doc:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        self._text = self.nlp(value)

    @staticmethod
    def from_ova(obj: Any, nlp: Language) -> Analysis:
        return Analysis(
            text=nlp(obj.get("plain_txt")),
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
