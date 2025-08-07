# C:\Users\marco\agente_gemini\HASHIRU_6_1\tools\net.py
from __future__ import annotations

from pathlib import Path
import hashlib
import shlex
import requests

from utils.audit import audit_event


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _to_bool(val: str) -> bool:
    v = str(val).strip().lower()
    return not (v in {"0", "false", "no", "n"})


def _parse_args(args: str) -> dict:
    """
    Retorna um dicionário com:
      url(str), to(Path|None), timeout(int), verify(bool), ua(str),
      head(bool), headers(bool), max(int), hash(str|None)
    """
    tokens = shlex.split(args or "", posix=False)
    cfg = {
        "url": "",
        "to": None,            # Path|None
        "timeout": 20,         # segundos
        "verify": True,        # TLS
        "ua": "HASHIRU/1.0 (+https://local)",
        "head": False,
        "headers": False,
        "max": 1000,           # preview
        "hash": None,          # "sha256" | None
    }
    if not tokens:
        return cfg

    cfg["url"] = tokens[0]
    i = 1
    while i < len(tokens):
        t = tokens[i]
        # switches simples
        if t == "--head":
            cfg["head"] = True
            i += 1
            continue
        if t == "--headers":
            cfg["headers"] = True
            i += 1
            continue

        # switches com valor
        if t == "--to" and i + 1 < len(tokens):
            cfg["to"] = Path(tokens[i + 1]).resolve(strict=False)
            i += 2
            continue
        if t == "--timeout" and i + 1 < len(tokens):
            try:
                cfg["timeout"] = int(tokens[i + 1])
            except Exception:
                pass
            i += 2
            continue
        if t == "--verify" and i + 1 < len(tokens):
            cfg["verify"] = _to_bool(tokens[i + 1])
            i += 2
            continue
        if t == "--ua" and i + 1 < len(tokens):
            cfg["ua"] = tokens[i + 1]
            i += 2
            continue
        if t == "--max" and i + 1 < len(tokens):
            try:
                cfg["max"] = max(0, int(tokens[i + 1]))
            except Exception:
                pass
            i += 2
            continue
        if t == "--hash" and i + 1 < len(tokens):
            val = tokens[i + 1].strip().lower()
            cfg["hash"] = val if val in {"sha256"} else None
            i += 2
            continue

        # ignora token não reconhecido
        i += 1

    return cfg


async def handle_get(args: str, block: str) -> str:
    r"""
    /net:get URL [--to CAMINHO] [--timeout S] [--verify 0|1] [--ua "UA"]
                 [--head] [--headers] [--max N] [--hash sha256]

    Exemplos:
      /net:get https://httpbin.org/get --headers
      /net:get "https://example.com" --to C:\temp\ex.html --timeout 20
      /net:get https://httpbin.org/anything --head --headers
      /net:get https://example.com --to out.bin --hash sha256 --verify 1
    """
    cfg = _parse_args(args)
    url = cfg["url"]
    if not url:
        return ("Uso: /net:get <URL> [--to CAMINHO] [--timeout S] [--verify 0|1] "
                "[--ua UA] [--head] [--headers] [--max N] [--hash sha256]")

    headers = {"User-Agent": cfg["ua"]}

    try:
        if cfg["head"]:
            # HEAD
            r = requests.head(
                url,
                headers=headers,
                timeout=cfg["timeout"],
                allow_redirects=True,
                verify=cfg["verify"],
            )
            status = r.status_code
            lines = [f"🌐 HEAD {url}", f"HTTP {status}"]
            if cfg["headers"]:
                lines.append("**Headers:**")
                for k, v in r.headers.items():
                    lines.append(f"- {k}: {v}")
            audit_event("net_head", {"url": url, "code": status})
            return "\n".join(lines)

        # GET
        with requests.get(
            url,
            headers=headers,
            timeout=cfg["timeout"],
            stream=True,
            verify=cfg["verify"],
        ) as r:
            r.raise_for_status()

            if cfg["to"]:
                # salvar em disco
                cfg["to"].parent.mkdir(parents=True, exist_ok=True)
                total = 0
                with open(cfg["to"], "wb") as f:
                    for chunk in r.iter_content(1024 * 64):
                        if chunk:
                            f.write(chunk)
                            total += len(chunk)

                msg = [f"✅ Baixado: `{cfg['to']}` • {total} bytes • HTTP {r.status_code}"]
                if cfg["hash"] == "sha256":
                    try:
                        digest = _sha256_file(cfg["to"])
                        msg.append(f"SHA-256: `{digest}`")
                    except Exception as he:
                        msg.append(f"(falhou SHA-256: {he})")

                audit_event(
                    "net_get_save",
                    {"url": url, "path": str(cfg["to"]), "code": r.status_code, "bytes": total},
                )
                return "\n".join(msg)

            # pré-visualização do corpo (texto)
            text = r.text
            cut = text[: cfg["max"]]
            extra = "" if len(text) <= cfg["max"] else "\n...(truncado)"
            lines = [f"🌐 GET {url}", f"HTTP {r.status_code}"]
            if cfg["headers"]:
                lines.append("**Headers:**")
                for k, v in r.headers.items():
                    lines.append(f"- {k}: {v}")
            lines.append("**Body (preview):**")
            lines.append(f"```\n{cut}\n```{extra}")

            audit_event(
                "net_get_preview",
                {"url": url, "code": r.status_code, "preview_len": len(cut)},
            )
            return "\n".join(lines)

    except requests.exceptions.SSLError as e:
        return f"🔒 Erro TLS/SSL (tente `--verify 0` se você souber o que está fazendo): {e}"
    except requests.exceptions.Timeout:
        return f"⏳ Timeout após {cfg['timeout']}s em `{url}`"
    except requests.exceptions.HTTPError as e:
        status = getattr(e.response, "status_code", "N/A")
        return f"❌ HTTP {status}: {e}"
    except Exception as e:
        return f"💥 Erro /net:get {url}: {e}"
