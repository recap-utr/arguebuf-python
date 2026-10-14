from collections.abc import Iterable
from dataclasses import dataclass, replace

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

    def translate_graph(self, graph: ag.Graph) -> None:
        resources = list(graph.resources.values())

        for resource, translation in zip(
            resources,
            self.translate_texts(resource.plain_text for resource in resources),
            strict=True,
        ):
            resource.text = translation

        references = [
            (atom, atom.reference)
            for atom in graph.atom_nodes.values()
            if atom.reference is not None
        ]

        for (atom, reference), translation in zip(
            references,
            self.translate_texts(reference.plain_text for _, reference in references),
            strict=True,
        ):
            atom.reference = replace(reference, text=translation)

        atoms = list(graph.atom_nodes.values())

        for atom, translation in zip(
            atoms, self.translate_texts(atom.plain_text for atom in atoms), strict=True
        ):
            atom.text = translation

    def translate_graphs(self, graphs: Iterable[ag.Graph]) -> None:
        for graph in graphs:
            self.translate_graph(graph)
