from dataclasses import dataclass
from enum import Enum

__all__ = ("Format", "Config")


class Format(str, Enum):
    ARGUEBUF = "arguebuf"
    AIF = "aif"
    XAIF = "xaif"


@dataclass
class Config:
    format: Format = Format.ARGUEBUF
    prettify: bool = True


DefaultConfig = Config()
