from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

__all__ = ("Format", "Config")


class Format(Enum):
    ARGUEBUF = auto()
    AIF = auto()


@dataclass
class Config:
    format: Format = Format.ARGUEBUF
    prettify: bool = True


DefaultConfig = Config()
