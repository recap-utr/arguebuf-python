from enum import StrEnum

__all__ = ("Format",)


class Format(StrEnum):
    """Formats supported by `arguebuf.dump.dict`."""

    ARGUEBUF = "arguebuf"
    AIF = "aif"
    XAIF = "xaif"
