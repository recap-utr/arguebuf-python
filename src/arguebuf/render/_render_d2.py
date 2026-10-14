import subprocess
from pathlib import Path

from arguebuf.schemas.d2 import D2Graph

__all__ = ("d2",)


def d2(graph: D2Graph, path: Path | str) -> None:
    """Render a graph created by `arguebuf.dump.d2` using the `d2` executable.

    The output format (e.g., png, pdf, svg) is derived from the suffix of `path`.
    """
    subprocess.run(
        ["d2", "-", str(path)],
        input=str(graph),
        text=True,
        check=True,
        capture_output=True,
    )
