import copy
from collections.abc import Iterable
from dataclasses import dataclass

from deepl import DeepLClient, TextResult

import arguebuf as ag

__all__ = ("Translator",)


@dataclass(slots=True, frozen=True)
class Translator:
    """Translate texts and graphs with a DeepL client."""

    client: DeepLClient
    source_lang: str
    target_lang: str

    def translate_text(self, text: str) -> str:
        return self.translate_texts([text])[0]

    def translate_texts(self, texts: Iterable[str]) -> list[str]:
        texts = list(texts)

        if not texts:
            return []

        results = self.client.translate_text(
            texts,
            source_lang=self.source_lang,
            target_lang=self.target_lang,
            preserve_formatting=True,
        )

        if isinstance(results, TextResult):
            results = [results]

        return [result.text for result in results]

    def translate_graph(self, graph: ag.GraphDraft) -> list[ag.Issue]:
        """Translate the texts of a graph and re-anchor the translated references.

        Returns:
            The warnings of re-anchoring the references in the translated resources.
        """
        atoms = list(graph.atom_nodes.values())
        references = iter(
            self.translate_texts(
                atom.reference.text for atom in atoms if atom.reference is not None
            )
        )

        for atom, translation in zip(
            atoms, self.translate_texts(atom.text for atom in atoms), strict=True
        ):
            graph.update_atom(
                atom,
                text=translation,
                reference=None
                if atom.reference is None
                else copy.replace(atom.reference, text=next(references), offset=None),
            )

        resources = list(graph.resources.values())
        issues: list[ag.Issue] = []

        # translating a resource re-anchors the already translated references to it
        for resource, translation in zip(
            resources,
            self.translate_texts(resource.text for resource in resources),
            strict=True,
        ):
            issues.extend(graph.update_resource(resource, text=translation))

        return issues
