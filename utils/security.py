# -*- coding: utf-8 -*-
"""
utils/security.py
Políticas de escrita/leitura do projeto HASHIRU 6.1 centralizadas.

APIs:
- is_write_path_allowed(path: str | Path) -> bool
- assert_write_allowed(path: Path) -> None (lança PermissionError)
- project_root() -> Path

Regras:
- Restringe escrita a diretórios whitelisted.
- Bloqueia extensões perigosas e diretórios negados.
- Nunca permite escapar da raiz do projeto.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Union

PathLike = Union[str, Path]

# --- Raiz do projeto (pasta que contém "utils") ---
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]

# ===== Políticas de escrita e auto-mod =====
SELF_MODIFICATION = {
    "enabled": True,
    "auto_backup": False,  # sem backup
}

SECURITY_POLICY = {
    "ALLOWED_WRITE_DIRS": [
        ".", "tools", "utils", "scripts", "artifacts"
    ],
    "DENIED_DIRS": [
        ".git", "backups", "__pycache__", "hashiru_6_env",
        "venv", ".venv", "node_modules", "dist", "build",
    ],
    "DENIED_EXTS": [".bat", ".cmd", ".ps1", ".exe", ".dll"],
}

def _is_within(parent: Path, child: Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except Exception:
        return False

def _first_path_component(rel_path: Path) -> str:
    parts = rel_path.parts
    if not parts:
        return "."
    return parts[0]

def is_write_path_allowed(target_path: PathLike) -> bool:
    root = project_root()
    abs_target = (root / Path(target_path)).resolve()

    # Não sair da raiz do projeto
    if not _is_within(root, abs_target):
        return False

    # Extensão negada
    if abs_target.suffix.lower() in (SECURITY_POLICY.get("DENIED_EXTS") or []):
        return False

    # Pasta negada (nível topo)
    rel = abs_target.relative_to(root)
    first = _first_path_component(rel)
    if first in set(SECURITY_POLICY.get("DENIED_DIRS") or []):
        return False

    # Permitidos (nível topo)
    allowed = set(SECURITY_POLICY.get("ALLOWED_WRITE_DIRS") or [])
    return first in allowed

def assert_write_allowed(target_path: PathLike) -> None:
    if not is_write_path_allowed(target_path):
        raise PermissionError(f"Política de segurança: escrita negada em '{target_path}'.")
