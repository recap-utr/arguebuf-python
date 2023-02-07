from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

__all__ = ("Format", "Config")


class Format(Enum):
    ARGUEBUF = "arguebuf"
    AIF = "aif"


@dataclass
class Config:
    format: Format = Format.ARGUEBUF
    prettify: bool = True


DefaultConfig = Config()
