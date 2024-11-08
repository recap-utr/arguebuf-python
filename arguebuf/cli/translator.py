import logging
from collections.abc import Iterable
from functools import singledispatchmethod

from deepl.translator import Translator as DeepLTranslator

import arguebuf as ag

log = logging.getLogger(__name__)


class Translator:
    translator: DeepLTranslator
    source_lang: str
    target_lang: str

    def __init__(self, auth_key: str, source_lang: str, target_lang: str):
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = DeepLTranslator(auth_key)

    def _deepl_translate(self, text: str | Iterable[str]) -> str | list[str]:
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

    @singledispatchmethod
    def translate(self, arg):
        raise NotImplementedError()

    @translate.register
    def _(self, arg: str) -> str:
        trans = self._deepl_translate(arg)
        assert isinstance(trans, str)
        return trans

    @translate.register
    def _(self, arg: Iterable[str]) -> list[str]:
        trans = self._deepl_translate(arg)
        assert isinstance(trans, list)
        return trans

    @translate.register
    def _(self, arg: ag.Graph) -> None:
        original_resources = [
            resource.plain_text for resource in arg.resources.values()
        ]
        for resource, translation in zip(
            arg.resources.values(), self.translate(original_resources), strict=True
        ):
            resource.text = translation

        references = [
            atom.reference.plain_text
            for atom in arg.atom_nodes.values()
            if atom.reference is not None
        ]
        for atom, translation in zip(
            arg.atom_nodes.values(), self.translate(references), strict=True
        ):
            if atom.reference is not None:
                atom.reference.text = translation

        atoms = [atom.plain_text for atom in arg.atom_nodes.values()]
        for atom, translation in zip(
            arg.atom_nodes.values(), self.translate(atoms), strict=True
        ):
            atom.text = translation

    @translate.register
    def _(self, arg: Iterable[ag.Graph]) -> None:
        for elem in arg:
            self.translate(elem)
