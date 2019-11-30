from __future__ import absolute_import, annotations

from dataclasses import dataclass, field
from typing import Union

from spacy.language import Language
from spacy.tokens import Doc, Span
import pendulum

from . import utils, dt


@dataclass
class Analysis:
    """Needed to store metadata for OVA."""

    ova_version: str = None
    text: Union[None, str, Doc, Span] = None
    annotated_text: str = None
    annotator_name: str = None
    document_source: str = None
    document_title: str = None
    document_date: pendulum.DateTime = field(default_factory=pendulum.now)

    # TODO: Implement annotated text without duplication
    # @property
    # def annotated_text(self):
    #     return self.text

    @staticmethod
    def from_ova(obj: Any, nlp: Optional[Language] = None) -> Analysis:
        return Analysis(
            ova_version=obj.get("ovaVersion"),
            text=utils.parse(obj.get("plain_txt"), nlp),
            annotated_text=obj.get("txt"),
            annotator_name=obj.get("annotatorName"),
            document_source=obj.get("documentSource"),
            document_title=obj.get("documentTitle"),
            document_date=dt.from_analysis(obj.get("documentDate")),
        )

    def to_ova(self) -> dict:
        return {
            "ovaVersion": self.ova_version or "",
            "txt": self.annotated_text or "",
            "plain_txt": self.text or "",
            "annotatorName": self.annotator_name or "",
            "documentSource": self.document_source or "",
            "documentTitle": self.document_title or "",
            "documentDate": dt.to_analysis(self.document_date),
        }
