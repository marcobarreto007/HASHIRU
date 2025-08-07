# C:\Users\marco\agente_gemini\HASHIRU_6_1\tools\pyexec.py
from __future__ import annotations

import ast
import io
import textwrap
from contextlib import redirect_stdout
from typing import Any

from config import PY_UNSAFE_DEFAULT
from utils.audit import audit_event


SAFE_BUILTINS: dict[str, Any] = {
    "print": print,
    "len": len,
    "range": range,
    "min": min,
    "max": max,
    "sum": sum,
    "enumerate": enumerate,
    "sorted": sorted,
    "int": int,
    "float": float,
    "str": str,
    "bool": bool,
    "list": list,
    "dict": dict,
    "set": set,
    "tuple": tuple,
    "abs": abs,
    "round": round,
    "zip": zip,
    "any": any,
    "all": all,
}


def _has_forbidden_nodes(tree: ast.AST) -> tuple[bool, str]:
    """Detecta importações e acessos perigosos no modo SAFE."""
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return True, "Uso de import não é permitido no modo SAFE."
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec", "__import__", "open"}:
                return True, f"Uso de {node.func.id} não é permitido no modo SAFE."
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            # bloqueios básicos a módulos típicos
            if node.value.id in {"os", "sys", "subprocess", "pathlib"}:
                return True, f"Acesso a {node.value.id} não é permitido no modo SAFE."
    return False, ""


def _parse_flags(args: str) -> dict[str, Any]:
    """
    Interpreta flags:
      --unsafe  (exige token CONFIRMO)
      --preview (não executa; apenas mostra o código detectado)
    """
    tokens = args.split()
    flags = {"unsafe": False, "preview": False, "confirmed": False, "rest": ""}

    # Varre tokens preservando ordem e coletando o restante
    rest = []
    for t in tokens:
        tl = t.lower()
        if tl == "--unsafe":
            flags["unsafe"] = True
        elif tl == "--preview":
            flags["preview"] = True
        elif tl == "confirmo":
            flags["confirmed"] = True
        else:
            rest.append(t)
    flags["rest"] = " ".join(rest).strip()
    return flags


def _normalize_block(block: str) -> str:
    if not block:
        return ""
    # Remove indent acidental e quebras supérfluas
    return textwrap.dedent(block).strip("\n\r ")


async def handle_py(args: str, block: str) -> str:
    """
    /py <<<codigo>>>               -> Modo SAFE
    /py --unsafe CONFIRMO <<<...>>> -> Modo UNSAFE (permite import)

    Regras:
      - SAFE: sem import, sem eval/exec/__import__/open/os/sys/subprocess.
      - UNSAFE: requer --unsafe e CONFIRMO.
      - --preview: apenas retorna o código detectado (sem executar).
    """
    flags = _parse_flags(args)
    code = _normalize_block(block)

    if flags["preview"]:
        preview = code if code else "(vazio)"
        return "**Preview de código (/py)**\n```\n" + preview[:6000] + "\n```"

    if not code:
        return "Uso: /py [--unsafe CONFIRMO] [--preview] <<<código Python>>>"

    try:
        if flags["unsafe"] or PY_UNSAFE_DEFAULT:
            # Segurança: requer confirmação explícita
            if not flags["confirmed"]:
                return (
                    "⚠️ Modo UNSAFE requer confirmação explícita.\n"
                    "Use: `/py --unsafe CONFIRMO <<<seu código>>>`"
                )
            audit_event("pyexec_unsafe", {"preview": False})

            # Execução "plena" (o usuário assume os riscos)
            buf = io.StringIO()
            glb: dict[str, Any] = {}
            loc: dict[str, Any] = {}
            with redirect_stdout(buf):
                exec(code, glb, loc)  # noqa: S102 - exec aprovado no modo UNSAFE
            output = buf.getvalue()
            if not output.strip():
                output = "_(sem saída)_"
            if len(output) > 6000:
                output = output[:6000] + "\n...[truncado]..."
            return "**/py (UNSAFE)**\n```\n" + output + "\n```"

        # Modo SAFE
        audit_event("pyexec_safe", {"preview": False})
        # Parse/AST + checagens
        tree = ast.parse(code, mode="exec")
        bad, reason = _has_forbidden_nodes(tree)
        if bad:
            return f"🚫 Bloqueado no modo SAFE: {reason}"

        buf = io.StringIO()
        safe_globals = {"__builtins__": SAFE_BUILTINS}
        safe_locals: dict[str, Any] = {}
        with redirect_stdout(buf):
            exec(compile(tree, "<safe>", "exec"), safe_globals, safe_locals)
        output = buf.getvalue()
        if not output.strip():
            output = "_(sem saída)_"
        if len(output) > 6000:
            output = output[:6000] + "\n...[truncado]..."
        return "**/py (SAFE)**\n```\n" + output + "\n```"

    except SyntaxError as e:
        return f"❌ Erro de sintaxe em /py: {e}"
    except Exception as e:
        return f"❌ Erro em /py: {e}"


# Alias para compatibilidade, caso o roteador espere outro nome
handle_pyexec = handle_py
