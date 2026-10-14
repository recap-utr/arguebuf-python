from typing import TextIO

from arguebuf.model import Graph

from ._config import Config
from ._load_aml import load_aml
from ._load_brat import load_brat
from ._load_json import load_json
from ._load_microtexts import load_microtexts
from ._load_text import load_text

__all__ = ("load_io",)


def load_io[T = str](
    obj: TextIO,
    suffix: str,
    name: str | None = None,
    config: Config[T] = Config(),
) -> Graph[T]:
    """Generate Graph structure from a file object based on the file `suffix`."""
    match suffix:
        case ".ann":
            return load_brat(obj, name, config)
        case ".txt":
            return load_text(obj, name, config)
        case ".aml":
            return load_aml(obj, name, config)
        case ".xml":
            return load_microtexts(obj, name, config)
        case _:
            return load_json(obj, name, config)
