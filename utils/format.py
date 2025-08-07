# -*- coding: utf-8 -*-
"""
Formatting utilities for consistently presenting data to the user.
"""
from typing import Any

def coalesce(*values: Any, default: Any = "") -> Any:
    """Returns the first non-None value in the provided arguments."""
    return next((v for v in values if v is not None), default)

def fmt_bytes(n: int) -> str:
    """Formats an integer number of bytes into a human-readable string."""
    if not isinstance(n, int) or n < 0:
        return "N/A"
    if n == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    p = 1024.0
    i = 0
    val = float(n)
    while val >= p and i < len(units) - 1:
        val /= p
        i += 1
    return f"{int(val)} {units[i]}" if i == 0 else f"{val:.2f} {units[i]}"

def fmt_list(title: str, items: list[str]) -> str:
    """Formats a list of strings into a titled, bulleted list."""
    if not items:
        return f"{title}\n- (vazio)"
    header = f"{title}\n"
    body = "\n".join(f"- {item}" for item in items)
    return header + body

def truncate(text: str, limit: int) -> str:
    """Truncates a string if it exceeds the specified limit, adding an indicator."""
    if not isinstance(text, str) or len(text) <= limit:
        return text
    if limit <= 20:
        return text[:limit]
    return text[:limit - 15] + "...[truncado]..."
