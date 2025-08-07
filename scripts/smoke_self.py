# scripts/smoke_self.py
# Teste rápido dos comandos /self via dispatcher, com saída UTF-8 e fallback para arquivo.
import os
import sys
import io
import asyncio
import pathlib

# --- Força UTF-8 no console e no Python, sem quebrar se não suportar ---
try:
    os.system("chcp 65001 >NUL 2>&1")
except Exception:
    pass

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    else:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

os.environ["PYTHONIOENCODING"] = "utf-8"

# --- Garante que o diretório raiz do projeto (pai de scripts/) esteja no sys.path ---
THIS_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = THIS_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- Imports do projeto (agora deve funcionar) ---
from tools import registry  # noqa: E402

ARTIFACTS = PROJECT_ROOT / "artifacts"
ARTIFACTS.mkdir(exist_ok=True)

def safe_print(text: str = "") -> None:
    """Imprime sem quebrar por Unicode, e faz fallback se necessário."""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            print(text.encode("utf-8", "replace").decode("utf-8"))
        except Exception:
            print(text.encode("ascii", "ignore").decode("ascii"))

async def main():
    out_lines = []
    safe_print(">> /self")
    out = await registry.dispatch("/self", "")
    safe_print(out)
    out_lines.append(">> /self\n" + out)

    safe_print("\n>> /self:status")
    out = await registry.dispatch("/self:status", "")
    safe_print(out)
    out_lines.append("\n>> /self:status\n" + out)

    safe_print("\n>> /self:analyze (primeiros 400 chars)")
    out = await registry.dispatch("/self:analyze", "")
    safe_print(out[:400])
    out_lines.append("\n>> /self:analyze\n" + out)

    out_text = "\n\n".join(out_lines)
    out_file = ARTIFACTS / "smoke_out.txt"
    out_file.write_text(out_text, encoding="utf-8")
    safe_print(f"\n[Saída completa salva em: {out_file.as_posix()}]")

if __name__ == "__main__":
    asyncio.run(main())
