# scripts/ping_ollama.py
# -*- coding: utf-8 -*-

# --- sys.path bootstrap: permite importar main_agent do diretório raiz ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -------------------------------------------------------------------------

import os, asyncio, json
import httpx
from main_agent import agent

async def get_installed_models(base_url: str) -> list[str]:
    """Consulta o Ollama e retorna a lista de modelos instalados (nome com tag)."""
    try:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{base_url}/api/tags")
            r.raise_for_status()
            data = r.json() or {}
            return [m.get("name") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []

async def main():
    base = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = os.environ.get("OLLAMA_TEST_MODEL")

    if not model:
        models = await get_installed_models(base)
        if not models:
            print(
                "Nenhum modelo instalado no Ollama.\n"
                "Rode:\n"
                "  ollama list\n"
                "  ollama pull llama3.1:8b   (ou)\n"
                "  ollama pull qwen2.5:7b\n"
                "Depois defina OLLAMA_TEST_MODEL=<nome exato que aparece em 'ollama list'> e rode novamente."
            )
            return
        model = models[0]
        print(f"[auto] Usando modelo instalado: {model}")

    payload = {"model": model, "prompt": "ping", "stream": False}

    try:
        out = await agent._post_ollama(base, payload, timeout=20)
        print("OK:", (out or "")[:240], "...")
    except httpx.HTTPStatusError as e:
        # Mostra corpo do erro do Ollama (exibe 'model not found' etc.)
        body = e.response.text if e.response is not None else ""
        code = e.response.status_code if e.response is not None else "N/A"
        print(f"HTTPStatusError {code}: {e}\nBody: {body[:500]}")
    finally:
        # Fecha o cliente http explicitamente (fora do ciclo do Chainlit)
        if getattr(agent, "http", None):
            try:
                await agent.http.aclose()
            except Exception:
                pass

if __name__ == "__main__":
    asyncio.run(main())
