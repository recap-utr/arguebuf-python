from __future__ import absolute_import, annotations

import uuid
from typing import Any, Optional, Callable


def unique_id() -> int:
    return uuid.uuid1().int >> 64


def xstr(data: Any) -> str:
    return "" if data is None else str(data)


def parse(text: str, nlp: Optional[Callable[[str], Any]]) -> Any:
    return nlp(text) if nlp else text
