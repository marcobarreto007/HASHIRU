# -*- coding: utf-8 -*-
"""
Path and filesystem related utilities.
"""
from pathlib import Path
from typing import Any, Union

def to_path(obj: Any) -> Path:
    """Converts a string or Path object to a resolved Path."""
    if isinstance(obj, Path):
        return obj.resolve(strict=False)
    if isinstance(obj, str):
        return Path(obj).resolve(strict=False)
    raise TypeError(f"Object of type {type(obj).__name__} cannot be converted to Path")

def is_binary_file(path: Union[str, Path], chunk_size: int = 1024) -> bool:
    """
    Heuristically determines if a file is binary by checking for null bytes.
    Returns True on read errors (assume not plain text).
    """
    try:
        file_path = to_path(path)
        if not file_path.is_file():
            return True
        with file_path.open("rb") as f:
            chunk = f.read(chunk_size)
        return b"\x00" in chunk
    except Exception:
        return True

def safe_glob(base: Union[str, Path], pattern: str) -> list[Path]:
    """
    Performs a glob search relative to a base path, handling exceptions.
    Returns a list of resolved Path objects.
    """
    try:
        base_path = to_path(base)
        if not base_path.is_dir():
            return []
        results = base_path.rglob(pattern) if "**" in pattern else base_path.glob(pattern)
        return [p.resolve(strict=False) for p in results if p.exists()]
    except Exception:
        return []
