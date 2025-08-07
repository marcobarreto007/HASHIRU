from __future__ import annotations
import importlib
from typing import Awaitable, Callable, Dict, Tuple
from utils.audit import audit_event

Handler = Callable[[str, str], Awaitable[str]]

# Rotas estáticas (opcional)
ROUTE_MAP: Dict[str, Tuple[str, str]] = {
    "/read": ("tools.fs", "handle_read"),
    # ... (demais comandos que você já tem)

    # SELF (auto-modificação)
    "/self":        ("tools.selfmod", "handle_self_menu"),
    "/self:analyze": ("tools.selfmod", "handle_self_analyze"),
    "/self:plan":    ("tools.selfmod", "handle_self_plan"),
    "/self:apply":   ("tools.selfmod", "handle_self_apply"),
    "/self:status":  ("tools.selfmod", "handle_self_status"),
}

# Rotas dinâmicas registradas em runtime (ex.: /self:*)
_DYNAMIC_ROUTES: Dict[str, Handler] = {}
_HELP: Dict[str, str] = {}

def register(cmd: str, handler: Handler) -> None:
    _DYNAMIC_ROUTES[cmd.lower()] = handler

def set_help(cmd: str, text: str) -> None:
    _HELP[cmd.lower()] = text

async def dispatch(message_text: str, block: str) -> str:
    parts = (message_text or "").split(None, 1)
    if not parts:
        return "❓ Vazio. Use /help."

    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    # 1) checa rotas dinâmicas primeiro
    if cmd in _DYNAMIC_ROUTES:
        try:
            audit_event("dispatch", {"cmd": cmd, "args_preview": args[:200]})
        except Exception:
            pass
        try:
            return await _DYNAMIC_ROUTES[cmd](args, block)
        except Exception as e:
            return f"💥 Erro executando `{cmd}`: {e}"

    # 2) cai no mapa estático
    if cmd not in ROUTE_MAP:
        return f"❌ Comando não reconhecido: {cmd}\nUse /help."

    mod_name, fn_name = ROUTE_MAP[cmd]
    try:
        mod = importlib.import_module(mod_name)
        handler: Handler = getattr(mod, fn_name)  # type: ignore[assignment]
    except Exception as e:
        return f"💥 Erro ao carregar handler `{mod_name}.{fn_name}`: {e}"

    try:
        audit_event("dispatch", {"cmd": cmd, "args_preview": args[:200]})
    except Exception:
        pass

    try:
        return await handler(args, block)
    except Exception as e:
        return f"💥 Erro executando `{cmd}`: {e}"

# Objeto registry com os mesmos métodos
class _Registry:
    register = staticmethod(register)
    set_help = staticmethod(set_help)
    async def dispatch(self, message_text: str, block: str) -> str:
        return await dispatch(message_text, block)

registry = _Registry()
__all__ = ["dispatch", "registry", "register", "set_help"]
