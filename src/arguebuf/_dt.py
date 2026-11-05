from datetime import UTC, datetime

from google.protobuf.timestamp_pb2 import Timestamp

__all__ = (
    "from_format",
    "from_isoformat",
    "from_protobuf",
    "now",
    "to_format",
    "to_protobuf",
    "utc",
)


def now() -> datetime:
    """Get the current time in UTC."""
    return datetime.now(UTC)


def utc(value: datetime) -> datetime:
    """Convert a datetime to UTC, naive values are interpreted as UTC.

    Examples:
        >>> from datetime import timedelta, timezone
        >>> utc(datetime(2020, 1, 1, 12, tzinfo=timezone(timedelta(hours=2))))
        datetime.datetime(2020, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
        >>> utc(datetime(2020, 1, 1, 12))
        datetime.datetime(2020, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    """
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def from_format(text: str | None, format: str) -> datetime | None:
    """Parse a timestamp in UTC, returns None for missing values and raises for malformed ones.

    Examples:
        >>> from_format("2020-01-01 12:00:00+0200", "%Y-%m-%d %H:%M:%S%z")
        datetime.datetime(2020, 1, 1, 10, 0, tzinfo=datetime.timezone.utc)
    """
    return utc(datetime.strptime(text, format)) if text else None


def from_isoformat(text: str | None) -> datetime | None:
    """Parse an ISO 8601 timestamp in UTC, returns None for missing values and raises for malformed ones."""
    return utc(datetime.fromisoformat(text)) if text else None


def to_format(value: datetime, format: str) -> str:
    """Format a timestamp in UTC.

    Examples:
        >>> from datetime import timedelta, timezone
        >>> value = datetime(2020, 1, 1, 12, tzinfo=timezone(timedelta(hours=2)))
        >>> to_format(value, "%Y-%m-%d %H:%M:%S")
        '2020-01-01 10:00:00'
    """
    return utc(value).strftime(format)


def from_protobuf(value: Timestamp) -> datetime:
    """Convert a protobuf timestamp to a datetime in UTC."""
    return value.ToDatetime(UTC)


def to_protobuf(value: datetime | None) -> Timestamp | None:
    """Convert a datetime to a protobuf timestamp, returns None for missing values.

    Examples:
        >>> from_protobuf(to_protobuf(datetime(2020, 1, 1, 12)))
        datetime.datetime(2020, 1, 1, 12, 0, tzinfo=datetime.timezone.utc)
    """
    if value is None:
        return None

    timestamp = Timestamp()
    timestamp.FromDatetime(utc(value))

    return timestamp
