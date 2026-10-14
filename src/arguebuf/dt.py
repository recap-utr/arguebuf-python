from datetime import UTC, datetime

__all__ = (
    "from_format",
    "from_isoformat",
    "now",
    "to_format",
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
