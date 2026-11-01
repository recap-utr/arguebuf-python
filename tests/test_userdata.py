import copy
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal, assert_type

import pytest

import arguebuf as ag
from arguebuf import JsonObject
from arguebuf.load._helpers import Context, add_edge


@dataclass(slots=True)
class AtomData:
    label: str
    # internal data that is never persisted
    embedding: list[float] = field(default_factory=list)


class AtomCodec:
    def validate_python(self, obj: JsonObject, /) -> AtomData:
        if not isinstance(label := obj.get("label"), str):
            raise TypeError(f"Invalid label {label!r}.")

        return AtomData(label)

    def dump_python(
        self, instance: AtomData, /, *, mode: Literal["json"]
    ) -> JsonObject:
        return {"label": instance.label}


class TypeAdapterLike[T]:
    """Signatures of `pydantic.TypeAdapter` (2.13): extra keyword parameters, `Any` results."""

    def __init__(
        self, load: Callable[[JsonObject], T], dump: Callable[[T], JsonObject]
    ) -> None:
        self.load, self.dump = load, dump

    def validate_python(
        self,
        object: Any,
        /,
        *,
        strict: bool | None = None,
        extra: Literal["allow", "ignore", "forbid"] | None = None,
        from_attributes: bool | None = None,
        context: Any | None = None,
        experimental_allow_partial: bool
        | Literal["off", "on", "trailing-strings"] = False,
        by_alias: bool | None = None,
        by_name: bool | None = None,
    ) -> T:
        return self.load(object)

    def dump_python(
        self,
        instance: T,
        /,
        *,
        mode: Literal["json", "python"] = "python",
        include: set[str] | None = None,
        exclude: set[str] | None = None,
        by_alias: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        exclude_computed_fields: bool = False,
        round_trip: bool = False,
        warnings: bool | Literal["none", "warn", "error"] = True,
        fallback: Callable[[Any], Any] | None = None,
        serialize_as_any: bool = False,
        polymorphic_serialization: bool | None = None,
        context: Any | None = None,
    ) -> Any:
        return self.dump(instance)


def _graph() -> tuple[ag.Graph[AtomData], AtomData]:
    data = AtomData("claim", [0.1, 0.2])
    g: ag.GraphDraft[AtomData] = ag.GraphDraft()
    g.add_node(ag.AtomNode("Claim", userdata=data, id="a"))

    return g.freeze(), data


def test_codec_roundtrip():
    g, data = _graph()
    codecs = ag.Codecs(atom=AtomCodec())
    obj = ag.dump.dict(g, codecs=codecs)
    loaded = ag.load.dict(obj, codecs=codecs)

    assert_type(codecs, ag.Codecs[AtomData])
    assert_type(loaded, ag.Graph[AtomData])
    assert_type(loaded.atom_nodes["a"].userdata, AtomData)
    assert loaded.atom_nodes["a"].userdata == AtomData("claim")
    # copies keep the internal data that the codec does not dump
    assert copy.deepcopy(g).atom_nodes["a"].userdata == data

    with pytest.raises(TypeError, match="Invalid label"):
        ag.load.dict(
            {**obj, "nodes": {"a": {"atom": {"text": "Claim"}}}}, codecs=codecs
        )


def test_type_adapter_shape():
    codecs = ag.Codecs(
        atom=TypeAdapterLike(AtomCodec().validate_python, lambda x: {"label": x.label})
    )
    g, _ = _graph()
    loaded = ag.load.dict(ag.dump.dict(g, codecs=codecs), codecs=codecs)

    assert_type(codecs, ag.Codecs[AtomData])
    assert loaded.atom_nodes["a"].userdata == AtomData("claim")


def test_default_roundtrip():
    g = ag.GraphDraft(userdata={"topic": "t"})
    g.add_node(ag.AtomNode("Claim", userdata={"n": [1, None]}, id="a"))
    loaded = ag.load.dict(ag.dump.dict(g.freeze()))

    assert_type(loaded, ag.Graph)
    assert_type(loaded.atom_nodes["a"].userdata, JsonObject)
    assert loaded.userdata == {"topic": "t"}
    assert loaded.atom_nodes["a"].userdata == {"n": [1, None]}
    assert ag.AtomNode("x").userdata is not ag.AtomNode("y").userdata


def test_repaired_edges_keep_required_userdata_and_metadata() -> None:
    graph: ag.GraphDraft[JsonObject, JsonObject, AtomData] = ag.GraphDraft()
    graph.add_node(ag.AtomNode("A", id="a"))
    graph.add_node(ag.AtomNode("B", id="b"))
    metadata = ag.Metadata()
    issues: list[ag.Issue] = []
    context = Context(ag.Codecs(edge=AtomCodec()), on_issue=issues.append)
    add_edge(graph, context, "a", "b", "e", metadata, {"label": "required"})

    assert [issue.code for issue in issues] == ["atom-edge"]
    assert len(graph.edges) == 2
    assert graph.edges["e"].source == "a"

    for edge in graph.edges.values():
        assert edge.userdata == AtomData("required")
        assert edge.metadata is metadata
