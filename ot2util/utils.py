"""Utilities."""
from typing import Union
from ot2util.config import PathLike


def write_file(contents: Union[str, bytes], path: PathLike) -> None:
    mode = "wb" if isinstance(contents, bytes) else "w"
    with open(path, mode) as f:
        f.write(contents)
