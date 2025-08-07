# C:\Users\marco\agente_gemini\HASHIRU_6_1\config.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Carrega .env se existir (não falha se não existir)
load_dotenv()

# ---------- Helpers robustos de leitura ----------
def _get_env_str(key: str, default: str) -> str:
    val = os.getenv(key, default)
    return val if isinstance(val, str) and val.strip() != "" else default

def _get_env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw.strip())
    except Exception:
        return default

def _get_env_bool(key: str, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    raw = raw.strip().lower()
    return raw in ("1", "true", "yes", "y", "on")

def _get_env_list(key: str, default_csv: str) -> List[str]:
    raw = os.getenv(key, default_csv)
    items = [x.strip() for x in raw.split(",") if x.strip()]
    # dedup preservando ordem
    seen, out = set(), []
    for x in items:
        xl = x.lower()
        if xl not in seen:
            seen.add(xl)
            out.append(x)
    return out

# ---------- Diretórios base ----------
ROOT: Path = Path(__file__).parent.resolve()
DATA_DIR: Path = Path(_get_env_str("DATA_DIR", str(ROOT / "data"))).resolve()
LOGS_DIR: Path = Path(_get_env_str("LOGS_DIR", str(ROOT / "logs"))).resolve()

# Garante criação de pastas
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Rede/Servidor ----------
HOST: str = _get_env_str("HOST", "localhost")
PORT: int = _get_env_int("PORT", 8080)

# ---------- Flags/Defaults ----------
TIMEOUT_DEFAULT: int = _get_env_int("TIMEOUT_DEFAULT", 60)
AUDIT_ENABLED: bool = _get_env_bool("AUDIT_ENABLED", True)

_DELETE_MODE = _get_env_str("DELETE_MODE", "trash").lower()
if _DELETE_MODE not in {"trash", "hard"}:
    _DELETE_MODE = "trash"
DELETE_MODE: str = _DELETE_MODE  # "trash" | "hard"

PY_UNSAFE_DEFAULT: bool = _get_env_bool("PY_UNSAFE_DEFAULT", False)

# ---------- Exec allowlist ----------
EXEC_ALLOWLIST: List[str] = _get_env_list(
    "EXEC_ALLOWLIST",
    "cmd,ipconfig,ping,tracert,where,tasklist,python,git",
)

# ---------- Export explícito ----------
__all__ = [
    "ROOT",
    "DATA_DIR",
    "LOGS_DIR",
    "HOST",
    "PORT",
    "TIMEOUT_DEFAULT",
    "AUDIT_ENABLED",
    "DELETE_MODE",
    "PY_UNSAFE_DEFAULT",
    "EXEC_ALLOWLIST",
]
