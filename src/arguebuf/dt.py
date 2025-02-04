import pendulum
from google.protobuf import timestamp_pb2


def from_format(text: str | None, format: str) -> pendulum.DateTime | None:
    return pendulum.from_format(text, format) if text else None


def to_format(dt: pendulum.DateTime | None, format: str) -> str:
    return dt.format(format) if dt else ""


def from_protobuf(dt: timestamp_pb2.Timestamp) -> pendulum.DateTime:
    return pendulum.instance(dt.ToDatetime()) if dt else pendulum.now()


def to_protobuf(dt: pendulum.DateTime | None, obj: timestamp_pb2.Timestamp) -> None:
    if dt:
        obj.FromDatetime(dt)
