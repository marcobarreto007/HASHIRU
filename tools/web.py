# C:\Users\marco\agente_gemini\HASHIRU_6_1\tools\web.py
from __future__ import annotations

import html
import shlex
from typing import List, Optional

import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

try:
    import trafilatura  # limpeza de conteúdo
except Exception:
    trafilatura = None  # segue com fallback


def _parse_search_args(args: str) -> dict:
    """
    /search termo [--max N] [--news] [--safesearch off|moderate|strict] [--site dominio]
    """
    tokens = shlex.split(args, posix=False)
    out = {
        "term": None,
        "max": 10,
        "news": False,
        "safesearch": "off",
        "site": None,
    }
    i = 0
    # termo = primeiro token não-flag (se quiser usar aspas, funciona)
    while i < len(tokens):
        t = tokens[i]
        if not t.startswith("--") and out["term"] is None:
            out["term"] = t
            i += 1
            break
        i += 1

    while i < len(tokens):
        t = tokens[i]
        if t == "--max" and i + 1 < len(tokens):
            try:
                out["max"] = int(tokens[i + 1])
            except:
                pass
            i += 2
        elif t == "--news":
            out["news"] = True
            i += 1
        elif t == "--safesearch" and i + 1 < len(tokens):
            level = tokens[i + 1].lower()
            if level in {"off", "moderate", "strict"}:
                out["safesearch"] = level
            i += 2
        elif t == "--site" and i + 1 < len(tokens):
            out["site"] = tokens[i + 1]
            i += 2
        else:
            i += 1
    return out


async def handle_search(args: str, block: str) -> str:
    """
    /search termo [--max N] [--news] [--safesearch off|moderate|strict] [--site dominio]

    Exemplos:
      /search rtx 4060 --max 5
      /search "python venv windows" --safesearch moderate
      /search chainlit --site github.com
      /search OpenAI --news --max 3
    """
    cfg = _parse_search_args(args)
    term = cfg["term"]
    if not term:
        return "Uso: /search <termo> [--max N] [--news] [--safesearch off|moderate|strict] [--site dominio]"

    # aplica filtro por site usando o próprio query
    if cfg["site"]:
        term = f"site:{cfg['site']} {term}"

    results: List[str] = []
    try:
        with DDGS() as ddgs:
            if cfg["news"]:
                src = ddgs.news(term, max_results=cfg["max"], safesearch=cfg["safesearch"])
            else:
                src = ddgs.text(term, max_results=cfg["max"], safesearch=cfg["safesearch"])

            for r in src or []:
                title = (r.get("title") or "").strip()
                href = r.get("href") or r.get("url") or ""
                body = (r.get("body") or r.get("snippet") or "").strip()
                if title:
                    title = title[:120]
                if body:
                    body = body[:200]
                item = []
                if title:
                    item.append(f"**{title}**")
                if body:
                    item.append(body)
                if href:
                    item.append(href)
                if item:
                    results.append("\n".join(item))

    except Exception as e:
        return f"💥 Erro na busca: {e}"

    if not results:
        return f"❌ Sem resultados para `{term}`."
    return f"🔎 Resultados para `{html.escape(term)}`:\n\n" + "\n\n".join(results)


def _parse_scrape_args(args: str) -> dict:
    """
    /scrape URL [--max N] [--headers] [--links] [--raw]
    """
    tokens = shlex.split(args, posix=False)
    out = {"url": None, "max": 2000, "headers": False, "links": False, "raw": False, "timeout": 30}
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if not t.startswith("--") and out["url"] is None:
            out["url"] = t
            i += 1
            break
        i += 1
    while i < len(tokens):
        t = tokens[i]
        if t == "--max" and i + 1 < len(tokens):
            try:
                out["max"] = int(tokens[i + 1])
            except:
                pass
            i += 2
        elif t == "--headers":
            out["headers"] = True
            i += 1
        elif t == "--links":
            out["links"] = True
            i += 1
        elif t == "--raw":
            out["raw"] = True
            i += 1
        elif t == "--timeout" and i + 1 < len(tokens):
            try:
                out["timeout"] = int(tokens[i + 1])
            except:
                pass
            i += 2
        else:
            i += 1
    return out


def _clean_with_trafilatura(html_text: str, url: Optional[str]) -> Optional[str]:
    if trafilatura is None:
        return None
    try:
        return trafilatura.extract(
            html_text,
            include_links=False,
            include_comments=False,
            include_tables=False,
            url=url,
            favor_precision=True,
            include_formatting=False,
        )
    except Exception:
        return None


async def handle_scrape(args: str, block: str) -> str:
    """
    /scrape URL [--max N] [--headers] [--links] [--raw] [--timeout S]

    Exemplos:
      /scrape https://example.com
      /scrape https://news.ycombinator.com/ --max 1200 --links
      /scrape https://httpbin.org/html --headers --raw
    """
    cfg = _parse_scrape_args(args)
    url = cfg["url"]
    if not url:
        return "Uso: /scrape <URL> [--max N] [--headers] [--links] [--raw] [--timeout S]"

    try:
        r = requests.get(url, timeout=cfg["timeout"])
        r.raise_for_status()
    except requests.exceptions.Timeout:
        return f"⏳ Timeout após {cfg['timeout']}s em `{url}`"
    except requests.exceptions.HTTPError as e:
        code = getattr(e.response, "status_code", "N/A")
        return f"❌ HTTP {code}: {e}"
    except Exception as e:
        return f"💥 Erro requisitando `{url}`: {e}"

    # Puxa título com BS4
    soup = BeautifulSoup(r.text, "html.parser")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else "(sem título)"

    # Conteúdo
    if cfg["raw"]:
        text = soup.get_text(" ", strip=True)
    else:
        extracted = _clean_with_trafilatura(r.text, url)
        text = extracted if (extracted and extracted.strip()) else soup.get_text(" ", strip=True)

    preview = text[: cfg["max"]]
    extra = "" if len(text) <= cfg["max"] else "\n...(truncado)"

    lines: List[str] = [f"🕷️ `{title}`", f"HTTP {r.status_code} • {len(r.text)} bytes (HTML)"]
    if cfg["headers"]:
        lines.append("**Headers de resposta:**")
        for k, v in r.headers.items():
            lines.append(f"- {k}: {v}")
    if cfg["links"]:
        links = []
        for a in soup.find_all("a"):
            href = a.get("href")
            if href and href.strip():
                links.append(href.strip())
            if len(links) >= 20:
                break
        if links:
            lines.append("**Links (até 20):**")
            for l in links:
                lines.append(f"- {l}")

    lines.append("**Texto (preview):**")
    lines.append(f"```\n{preview}\n```{extra}")
    return "\n".join(lines)
