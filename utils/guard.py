# -*- coding: utf-8 -*-
"""
Security guard functions for command execution and other sensitive operations.
"""
import os
import re
import shlex
from pathlib import Path

# Try to get allowlist from config, else None
try:
    from config import EXEC_ALLOWLIST
    if not isinstance(EXEC_ALLOWLIST, list):
        EXEC_ALLOWLIST = None
except (ImportError, AttributeError):
    EXEC_ALLOWLIST = None

DEFAULT_ALLOWLIST = [
    "cmd", "ipconfig", "ping", "tracert", "where", "tasklist", "python", "git"
]

def get_allowlist() -> list[str]:
    """
    Priority:
      1) EXEC_ALLOWLIST from config.py (list)
      2) EXEC_ALLOWLIST env var (comma/semicolon/whitespace separated)
      3) DEFAULT_ALLOWLIST
    """
    if EXEC_ALLOWLIST is not None:
        return [str(c).lower() for c in EXEC_ALLOWLIST]
    env_val = os.environ.get("EXEC_ALLOWLIST")
    if env_val:
        return [c.lower() for c in re.split(r"[,;\s]+", env_val) if c]
    return DEFAULT_ALLOWLIST

def needs_confirmation_for_exec(cmd: str, allow: list[str]) -> bool:
    """
    True se o comando (token 0) não está na allowlist.
    """
    if not cmd:
        return True
    try:
        parts = shlex.split(cmd, posix=False)
        if not parts:
            return True
        base = parts[0].lower()
        base_name = Path(base).stem.lower()
        return base_name not in allow
    except Exception:
        return True
