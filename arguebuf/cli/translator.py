import logging
import typing as t

import deepl
from multimethod import multimethod

import arguebuf as ag

log = logging.getLogger(__name__)


class Translator:
    translator: deepl.Translator
    source_lang: str
    target_lang: str

    def __init__(self, auth_key: str, source_lang: str, target_lang: str):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = deepl.Translator(auth_key)

    def _deepl_translate(
        self, text: t.Union[str, t.Iterable[str]]
    ) -> t.Union[str, t.List[str]]:
        result = self.translator.translate_text(
            text,
            source_lang=self.source_lang,
            target_lang=self.target_lang,
            preserve_formatting=True,
        )
        if isinstance(result, list):
            return [entry.text for entry in result]
        else:
            return result.text

    @multimethod
    def translate(self):
        raise NotImplementedError()

    @translate.register
    def _(self, text: str) -> str:
        trans = self._deepl_translate(text)
        assert isinstance(trans, str)
        return trans

    @translate.register
    def _(self, texts: t.Iterable[str]) -> t.List[str]:
        trans = self._deepl_translate(texts)
        assert isinstance(trans, list)
        return trans

    @translate.register
    def _(self, graph: ag.Graph) -> None:
        original_resources = [
            resource.plain_text for resource in graph.resources.values()
        ]
        for resource, translation in zip(
            graph.resources.values(), self.translate(original_resources)
        ):
            resource.text = translation

        references = [
            atom.reference.plain_text
            for atom in graph.atom_nodes.values()
            if atom.reference is not None
        ]
        for atom, translation in zip(
            graph.atom_nodes.values(), self.translate(references)
        ):
            if atom.reference is not None:
                atom.reference.text = translation

        atoms = [atom.plain_text for atom in graph.atom_nodes.values()]
        for atom, translation in zip(graph.atom_nodes.values(), self.translate(atoms)):
            atom.text = translation

    @translate.register
    def _(self, graphs: t.Iterable[ag.Graph]) -> None:
        for graph in graphs:
            self.translate(graph)
