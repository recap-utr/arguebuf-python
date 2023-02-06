import typing as t

import pendulum
from google.protobuf import timestamp_pb2
from pendulum.datetime import DateTime


def from_format(text: t.Optional[str], format: str) -> t.Optional[DateTime]:
    return pendulum.from_format(text, format) if text else None


def to_format(dt: t.Optional[DateTime], format: str) -> str:
    return dt.format(format) if dt else ""


def from_protobuf(dt: timestamp_pb2.Timestamp) -> DateTime:
    return pendulum.instance(dt.ToDatetime()) if dt else pendulum.now()


def to_protobuf(dt: t.Optional[DateTime], obj: timestamp_pb2.Timestamp) -> None:
    if dt:
        obj.FromDatetime(dt)
