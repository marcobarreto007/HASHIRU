# C:\Users\marco\agente_gemini\HASHIRU_6_1\scripts\opt_http_client_patch.py
from __future__ import annotations

import re, ast, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "main_agent.py"

def read_text(p: pathlib.Path) -> str:
    return p.read_text(encoding="utf-8")

def write_text(p: pathlib.Path, s: str) -> None:
    p.write_text(s, encoding="utf-8")

def ensure_http_client_init(src: str) -> tuple[str, bool]:
    """
    Insere em __init__:
        self.http: Optional[httpx.AsyncClient] = httpx.AsyncClient()
    logo após:
        self.reinforcement_data: List[Dict[str, Any]] = []
    Se já existir, não duplica.
    """
    if "self.http: Optional[httpx.AsyncClient] = httpx.AsyncClient()" in src:
        return src, False

    anchor = r"(self\.reinforcement_data:\s*List\[Dict\[str,\s*Any\]\]\s*=\s*\[\]\s*)"
    if re.search(anchor, src):
        patched = re.sub(
            anchor,
            r"\1\n        # Reutiliza um único cliente HTTP (melhor performance)\n"
            r"        self.http: Optional[httpx.AsyncClient] = httpx.AsyncClient()",
            src, count=1, flags=re.M
        )
        return patched, True

    # Fallback: tenta inserir dentro de __init__ depois do último self.*
    m_init = re.search(r"class\s+AutonomousAgent\s*:\s*[\s\S]*?def\s+__init__\(", src)
    if m_init:
        # insere após primeira linha de __init__
        patched = re.sub(
            r"(\s*def\s+__init__\([^\)]*\):\s*\n)",
            r"\1        self.http: Optional[httpx.AsyncClient] = httpx.AsyncClient()\n",
            src, count=1
        )
        return patched, True

    return src, False

def replace_post_ollama(src: str) -> tuple[str, bool]:
    """
    Substitui o corpo de _post_ollama para usar self.http compartilhado,
    mantendo timeout por chamada e fallback com AsyncClient temporário.
    """
    if "client = getattr(self, \"http\", None)" in src and "temp_client.post(" in src:
        return src, False  # já está no formato novo

    new_post = (
        "async def _post_ollama(self, base_url: str, payload: Dict[str, Any], timeout: float) -> str:\n"
        "        \"\"\"\n"
        "        Usa o cliente HTTP compartilhado (self.http) para reduzir overhead de conexões.\n"
        "        Mantém compatibilidade passando timeout por requisição.\n"
        "        \"\"\"\n"
        "        client = getattr(self, \"http\", None)\n"
        "        if client is not None:\n"
        "            r = await client.post(f\"{base_url}/api/generate\", json=payload, timeout=timeout)\n"
        "            r.raise_for_status()\n"
        "            data = r.json()\n"
        "            return data.get(\"response\", \"\") or data.get(\"message\", \"\")\n"
        "        # Fallback defensivo (se por algum motivo self.http não existir)\n"
        "        import httpx as _httpx\n"
        "        async with _httpx.AsyncClient() as temp_client:\n"
        "            r = await temp_client.post(f\"{base_url}/api/generate\", json=payload, timeout=timeout)\n"
        "            r.raise_for_status()\n"
        "            data = r.json()\n"
        "            return data.get(\"response\", \"\") or data.get(\"message\", \"\")\n"
    )

    # Delimitar bloco do método dentro da classe (indent de 4 espaços) até o próximo método da classe
    # Começa no "async def _post_ollama(" com 4 espaços de indent
    m_start = re.search(r"^\s{4}async\s+def\s+_post_ollama\([^\n]*\):", src, flags=re.M)
    if not m_start:
        return src, False

    # Próximo método da classe (4 espaços + async def ) para fechar o bloco
    m_next = re.search(r"^\s{4}async\s+def\s+\w+\(", src[m_start.end():], flags=re.M)
    if m_next:
        start = m_start.start()
        end = m_start.end() + m_next.start()
    else:
        # até o fim do arquivo
        start = m_start.start()
        end = len(src)

    # Mantém indentação de 4 espaços
    new_block = "    " + new_post.replace("\n", "\n    ")
    patched = src[:start] + new_block + src[end:]
    return patched, True

def ensure_on_chat_end(src: str) -> tuple[str, bool]:
    """
    Adiciona hook @cl.on_chat_end que fecha agent.http se existir.
    """
    if "@cl.on_chat_end" in src:
        return src, False

    hook = (
        "@cl.on_chat_end\n"
        "async def on_chat_end():\n"
        "    try:\n"
        "        if hasattr(agent, \"http\") and agent.http is not None:\n"
        "            await agent.http.aclose()\n"
        "    except Exception:\n"
        "        # Evita quebrar o encerramento da sessão por erros de fechamento\n"
        "        pass\n"
    )
    if not src.endswith("\n"):
        src += "\n"
    src += "\n" + hook
    return src, True

def ensure_typing_optional(src: str) -> tuple[str, bool]:
    """
    Garante que Optional esteja importado (já costuma estar, mas checamos).
    """
    if re.search(r"from\s+typing\s+import\s+[^\\n]*Optional", src):
        return src, False
    # tenta acrescentar Optional na linha existente de typing
    src2, n = re.subn(
        r"(from\s+typing\s+import\s+)([^\n]+)",
        lambda m: m.group(1) + m.group(2).rstrip() + ", Optional",
        src, count=1
    )
    return (src2, n > 0)

def main():
    print(f"[patch] ROOT  = {ROOT}")
    print(f"[patch] FILE  = {TARGET}")
    src = read_text(TARGET)

    changed = False

    src, c1 = ensure_http_client_init(src); changed |= c1
    src, c2 = replace_post_ollama(src);    changed |= c2
    src, c3 = ensure_on_chat_end(src);     changed |= c3
    src, c4 = ensure_typing_optional(src); changed |= c4

    if changed:
        # valida sintaxe
        try:
            ast.parse(src)
        except SyntaxError as e:
            print("[patch] ERRO de sintaxe após patch:", e)
            sys.exit(2)
        write_text(TARGET, src)
    print(f"PATCH_APPLIED={changed}")

    # quick checks
    for needle in [
        "self.http: Optional[httpx.AsyncClient] = httpx.AsyncClient()",
        "async def _post_ollama(",
        "@cl.on_chat_end",
    ]:
        print("[check] contains:", needle, "=>", needle in src)

if __name__ == "__main__":
    main()
