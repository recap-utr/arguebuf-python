from dataclasses import dataclass
from enum import StrEnum

__all__ = ("Config", "DefaultConfig", "Format")


class Format(StrEnum):
    ARGUEBUF = "arguebuf"
    AIF = "aif"
    XAIF = "xaif"


@dataclass(slots=True, frozen=True)
class Config:
    """Options for dumping graphs.

    Attributes:
        format: Format of the exported graph.
        prettify: Indent the exported JSON.
    """

    format: Format = Format.ARGUEBUF
    prettify: bool = True


DefaultConfig = Config()
