# C:\Users\marco\agente_gemini\HASHIRU_6_1\tools\exec.py
from __future__ import annotations

import shlex
import subprocess

from config import TIMEOUT_DEFAULT
from utils.audit import audit_event
from utils.guard import get_allowlist, needs_confirmation_for_exec


def _parse_timeout(parts: list[str], default_timeout: int) -> tuple[list[str], int]:
    """Extrai --timeout N se existir."""
    timeout = default_timeout
    if "--timeout" in parts:
        try:
            i = parts.index("--timeout")
            timeout = int(parts[i + 1])
            parts = parts[:i] + parts[i + 2 :]
        except Exception:
            # parâmetro malformado -> ignora e mantém default
            pass
    return parts, timeout


async def handle_exec(args: str, block: str) -> str:
    """
    /exec <comando> [--timeout N]

    Regras:
      - Allowlist (ENV EXEC_ALLOWLIST). Se 1º token não estiver na allowlist, exige CONFIRMO:
        /exec CONFIRMO <comando>
      - --timeout N (segundos) sobrepõe TIMEOUT_DEFAULT.
    """
    if not args.strip():
        return "Uso: /exec <comando> [--timeout N]"

    # Parse básico (Windows-friendly)
    parts = shlex.split(args, posix=False)
    parts, timeout = _parse_timeout(parts, TIMEOUT_DEFAULT)

    # Monta comando final
    cmd = " ".join(parts).strip()
    if not cmd:
        return "Uso: /exec <comando> [--timeout N]"

    allow = get_allowlist()

    # Checagem de confirmação para fora da allowlist
    if needs_confirmation_for_exec(cmd, allow):
        if cmd.lower().startswith("confirmo "):
            cmd = cmd[len("confirmo ") :].lstrip()
        else:
            alw = ", ".join(allow) or "(vazia)"
            return (
                "⚠️ Comando fora da allowlist.\n"
                f"Allowlist: {alw}\n"
                "Se deseja executar mesmo assim, use:\n"
                f"`/exec CONFIRMO {cmd}`"
            )

    # Execução do comando
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        audit_event("exec", {"cmd": cmd, "rc": proc.returncode})

        out = (proc.stdout or "").strip()
        err = (proc.stderr or "").strip()

        lines = [f"✅ RC={proc.returncode}"]
        if out:
            if len(out) > 4000:
                out = out[:4000] + "\n...[truncado]..."
            lines.append("**STDOUT:**\n```\n" + out + "\n```")
        if err:
            if len(err) > 3000:
                err = err[:3000] + "\n...[truncado]..."
            lines.append("**STDERR:**\n```\n" + err + "\n```")
        if not out and not err:
            lines.append("_(sem saída)_")

        return "\n".join(lines)

    except subprocess.TimeoutExpired:
        audit_event("exec_timeout", {"cmd": cmd, "timeout": timeout})
        return f"⏳ Timeout ({timeout}s) executando: `{cmd}`"
    except Exception as e:
        audit_event("exec_error", {"cmd": cmd, "error": str(e)})
        return f"❌ Erro em /exec: {e}"
