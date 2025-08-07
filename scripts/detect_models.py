# scripts/detect_models.py
# -*- coding: utf-8 -*-
import os, asyncio
import httpx

async def main():
    base = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(f"{base}/api/tags")
            r.raise_for_status()
            data = r.json() or {}
            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
            if not models:
                print("Nenhum modelo instalado. Rode no terminal:")
                print("  ollama list")
                print("  ollama pull llama3.1:8b   (ou)")
                print("  ollama pull qwen2.5:7b")
                return
            print("Modelos instalados:")
            for name in models:
                print(" -", name)
    except Exception as e:
        print("Erro consultando /api/tags:", e)

if __name__ == "__main__":
    asyncio.run(main())
