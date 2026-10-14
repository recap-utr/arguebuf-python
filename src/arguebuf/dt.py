from datetime import UTC, datetime

# ty resolves the runtime module instead of the types-protobuf stubs
from google.protobuf.timestamp_pb2 import Timestamp  # ty: ignore[unresolved-import]

__all__ = (
    "from_format",
    "from_isoformat",
    "from_protobuf",
    "now",
    "to_format",
    "to_protobuf",
)


def now() -> datetime:
    return datetime.now(UTC)


def from_format(text: str | None, format: str) -> datetime | None:
    return datetime.strptime(text, format).replace(tzinfo=UTC) if text else None


def from_isoformat(text: str | None) -> datetime | None:
    if not text:
        return None

    value = datetime.fromisoformat(text)

    return value if value.tzinfo else value.replace(tzinfo=UTC)


def to_format(value: datetime | None, format: str) -> str:
    return value.strftime(format) if value else ""


def from_protobuf(obj: Timestamp) -> datetime:
    # unset timestamps are serialized as the epoch
    return obj.ToDatetime(UTC) if obj.seconds or obj.nanos else now()


def to_protobuf(value: datetime | None, obj: Timestamp) -> None:
    if value:
        obj.FromDatetime(value)
