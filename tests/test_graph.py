import json
from typing import Dict, Any, List

from deepdiff import DeepDiff
import recap_argument_graph as ag


def test_graph(shared_datadir):
    folder = shared_datadir / "in" / "graph"

    for file in folder.rglob("*.json"):
        with file.open() as f:
            raw = json.load(f)

        graph = ag.Graph.open(file)
        export = graph.to_dict()

        # TODO: Find more elegant alternative.
        if raw.get("analysis") and not raw["analysis"].get("documentDate"):
            del export["analysis"]["documentDate"]

        _clean_nodes(raw["nodes"])
        _clean_nodes(export["nodes"])
        _clean_edges(raw["edges"])
        _clean_edges(export["edges"])

        assert export == raw, file.name

        # assert (
        #         DeepDiff(
        #             raw,
        #             export,
        #             exclude_regex_paths={
        #                 r"root\['analysis'\]\['documentDate'\]",
        #                 r"root\['nodes'\]\[\d+\]\['text_length'\]",
        #                 r"root\['edges'\]\[\d+\]\['\w+'\]\['text_length'\]",
        #                 # TODO Remove color
        #                 r"root\['nodes'\]\[\d+\]\['color'\]",
        #                 r"root\['edges'\]\[\d+\]\['\w+'\]\['color'\]",
        #             },
        #         )
        #         == {}
        # ), file.name

        graph.render(shared_datadir / "out", "pdf")
        graph.to_nx()


_node_attrs = ("text_length", "color")


def _clean_nodes(nodes: List[Dict[str, Any]]) -> None:
    for node in nodes:
        _clean_node(node)


def _clean_node(node: Dict[str, Any]) -> None:
    for attr in _node_attrs:
        if node.get(attr) != None:
            del node[attr]


def _clean_edges(edges: List[Dict[str, Any]]) -> None:
    for edge in edges:
        for node in (edge.get("from"), edge.get("to")):
            _clean_node(node)
