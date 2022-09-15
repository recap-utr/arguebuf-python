import logging
import typing as t

import arguebuf as ag
import deepl_pro as dl

log = logging.getLogger(__name__)


class Translator:
    trans_plain: dl.Translator
    trans_xml: dl.Translator

    def __init__(self, auth_key: str, source_lang: str, target_lang: str):
        self.trans_plain = dl.Translator(
            auth_key,
            source_lang,
            target_lang,
            preserve_formatting=dl.Formatting.PRESERVE,
        )

        self.trans_xml = dl.Translator(
            auth_key,
            source_lang,
            target_lang,
            preserve_formatting=dl.Formatting.PRESERVE,
            tag_handling=dl.TagHandling.XML,
            outline_detection=dl.Outline.IGNORE,
        )

    def translate_graph(self, graph: ag.Graph, parallel: bool = False) -> None:
        # TODO: Use parallel request
        for resource in graph.resources.values():
            resource.text = self.trans_plain.translate_text(resource.plain_text)

        # TODO: Texts in the node anchors

        texts = [inode.plain_text for inode in graph.atom_nodes.values()]
        translations = self.trans_plain.translate_texts(texts, parallel=parallel)

        for inode, translation in zip(graph.atom_nodes.values(), translations):
            inode.text = translation

    def translate_graphs(
        self, graphs: t.Iterable[ag.Graph], parallel: bool = False
    ) -> None:
        for graph in graphs:
            self.translate_graph(graph, parallel)
