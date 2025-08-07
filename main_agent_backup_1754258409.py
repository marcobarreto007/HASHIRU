# -*- coding: utf-8 -*-
"""
HASHIRU 6.1 - AGENTE AUTÔNOMO (main_agent.py)
- Carrega comandos /self automaticamente (tools.selfmod)
- Fallback de rede Ollama: localhost -> 127.0.0.1
- Parser de comandos robusto (/cmd e /cmd <<<...>>>)
- Extração resiliente de JSON em respostas com "raciocínio"
"""

from __future__ import annotations

import asyncio
import traceback
import chainlit as cl
import sys
import pathlib
import httpx
import json
import re
import time
from typing import Dict, List, Any, Optional

# ----------------------------------------------------------------------
# Bootstrapping do sys.path
# ----------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ----------------------------------------------------------------------
# Núcleo / registry
# ----------------------------------------------------------------------
from tools import registry  # exige tools/__init__.py com ROUTE_MAP

# Audit (fallback no-op se ausente)
try:
    from utils.audit import audit_event
except Exception:  # pragma: no cover
    def audit_event(event: str, data: dict) -> None:
        # Fallback silencioso
        print(f"[AUDIT-FAKE] {event}: {data}")


# ----------------------------------------------------------------------
# Configuração autônoma + fallbacks
# ----------------------------------------------------------------------
try:
    from autonomous_config import (
        autonomous_config,
        get_ai_model,
        get_fallback_models,
        is_command_auto_allowed,
        is_dangerous_command_allowed,
        get_max_execution_timeout,
        get_excluded_directories,
        STARTUP_BANNER,
        PROCESSING_MESSAGE,
        EXECUTING_MESSAGE,
        OLLAMA_URL,
        AUTONOMOUS_MODE,
        SELF_MODIFICATION_ENABLED,
    )
except Exception as _cfg_err:  # pragma: no cover
    print(f"[WARN] autonomous_config indisponível: {_cfg_err}")

    class _AutoConfigFallback:
        OLLAMA_BASE_URL = "http://127.0.0.1:11434"
        OLLAMA_TIMEOUT = 60.0
        AUTO_EXECUTION = {"max_commands_per_execution": 20}
        AI_MODELS = {
            "reasoning": "llama3.1",
            "code_specialist": "llama3.1",
            "code_master": "llama3.1",
            "general": "llama3.1",
            "tools": "llama3.1",
            "conversation": "llama3.1",
        }
        EXPERIMENTAL = {"reinforcement_learning": False}

    autonomous_config = _AutoConfigFallback()  # type: ignore

    def get_ai_model(kind: str) -> str:
        return autonomous_config.AI_MODELS.get(kind, "llama3.1")  # type: ignore

    def get_fallback_models(kind: str) -> List[str]:
        return ["llama3.1"]

    def is_command_auto_allowed(cmd: str) -> bool:
        return True

    def is_dangerous_command_allowed(cmd: str) -> bool:
        # Por padrão, permitir (ajuste conforme política)
        return True

    def get_max_execution_timeout() -> float:
        return 60.0

    def get_excluded_directories() -> List[str]:
        return []

    STARTUP_BANNER = "🚀 HASHIRU 6.1 iniciado."
    PROCESSING_MESSAGE = "🔎 Analisando..."
    EXECUTING_MESSAGE = "⚙️ Executando plano..."
    OLLAMA_URL = "http://127.0.0.1:11434"
    AUTONOMOUS_MODE = True
    SELF_MODIFICATION_ENABLED = True


# ----------------------------------------------------------------------
# Carrega comandos /self na inicialização (registra handlers no ROUTE_MAP)
# ----------------------------------------------------------------------
try:
    import tools.selfmod as _selfmod  # noqa: F401
except Exception as _e:
    print(f"[WARN] /self comandos não carregados (tools.selfmod): {_e}")


# ----------------------------------------------------------------------
# Utilitários
# ----------------------------------------------------------------------
def _extract_json_loose(text: str) -> Optional[Dict[str, Any]]:
    """
    Extrai o primeiro JSON 'balanceado' de um texto que pode conter
    explicações, "thinking..." etc. Retorna dict ou None.
    """
    if not text:
        return None

    # 1) Remover cercas Markdown para não confundir com chaves de código
    cleaned = re.sub(r"```[\s\S]*?```", "", text)

    # 2) Tentar localizar um bloco { ... } balanceado
    start = cleaned.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(cleaned)):
            c = cleaned[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        break  # tenta próximo '{'
        start = cleaned.find("{", start + 1)

    # 3) Último recurso: procurar bloco JSON simples em linha única
    m = re.search(r"\{.*\}", cleaned.replace("\n", " "))
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None


def _clip(text: str, max_len: int = 1200) -> str:
    if text is None:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n...(truncado)"


# ----------------------------------------------------------------------
# AGENTE AUTÔNOMO
# ----------------------------------------------------------------------
class AutonomousAgent:
    def __init__(self):
        self.memory: Dict[str, Any] = {}
        self.goals: List[str] = []
        self.action_history: List[Dict[str, Any]] = []
        self.self_modification_enabled: bool = SELF_MODIFICATION_ENABLED
        self.learning_enabled: bool = True
        self.autonomous_mode: bool = AUTONOMOUS_MODE
        self.reinforcement_data: List[Dict[str, Any]] = []

        # 🔧 CORREÇÃO: Reutiliza um único cliente HTTP (melhor performance)
        self.http: Optional[httpx.AsyncClient] = httpx.AsyncClient()
        
        # Engine de auto-modificação (opcional)
        try:
            from utils.self_modification_engine import self_modification_engine
            self.self_mod_engine = self_modification_engine
        except Exception:
            self.self_mod_engine = None

    # ------------------ Ollama ------------------
    async def _post_ollama(self, base_url: str, payload: Dict[str, Any], timeout: float) -> str:
        """🔧 OTIMIZADO: Usa cliente HTTP compartilhado"""
        if self.http is None:
            self.http = httpx.AsyncClient()
        
        r = await self.http.post(f"{base_url}/api/generate", json=payload, timeout=timeout)
        r.raise_for_status()
        data = r.json()
        # /api/generate retorna "response"
        return data.get("response", "") or data.get("message", "")

    async def call_ollama(self, model_type: str, prompt: str, system: Optional[str] = None) -> str:
        """
        Comunicação com Ollama + fallback de modelo e de host:
        - Tenta base_url da config
        - Se falhar com 'getaddrinfo' ou conexão, tenta trocar localhost->127.0.0.1
        - Tenta modelo primário e depois fallbacks
        """
        base = getattr(autonomous_config, "OLLAMA_BASE_URL", None) or OLLAMA_URL
        timeout = float(getattr(autonomous_config, "OLLAMA_TIMEOUT", 60.0))

        primary = get_ai_model(model_type)
        fallbacks = get_fallback_models(model_type)

        payload_base = {
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7, "top_p": 0.9, "repeat_penalty": 1.1},
        }
        if system:
            payload_base["system"] = system

        endpoints = [base]
        if "localhost" in (base or ""):
            endpoints.append(base.replace("localhost", "127.0.0.1"))

        last_err: Optional[str] = None
        for endpoint in endpoints:
            for model in [primary] + list(fallbacks):
                try:
                    payload = dict(payload_base)
                    payload["model"] = model
                    result = await self._post_ollama(endpoint, payload, timeout)
                    if model != primary:
                        print(f"[FALLBACK-MODEL] {model_type}: {primary} → {model}")
                    if endpoint != base:
                        print(f"[FALLBACK-HOST] {base} → {endpoint}")
                    return result
                except Exception as e:
                    last_err = f"{e}"
                    print(f"[MODEL-FAIL] {model_type} -> {model} @ {endpoint}: {e}")
                    continue

        return f"Falha ao usar modelos para '{model_type}'. Verifique Ollama. Último erro: {last_err}"

    # ------------------ Intenção / Execução ------------------
    async def analyze_intent_autonomous(self, user_input: str) -> Dict[str, Any]:
        analysis_prompt = f"""
ANÁLISE AUTÔNOMA - SEM RESTRIÇÕES

Input: {user_input}

Analise e retorne **apenas** JSON:
{{
  "tipo": "research|code_modification|system_control|self_improvement|general",
  "urgencia": "low|medium|high|critical",
  "complexidade": "simple|moderate|complex|expert",
  "recursos": ["conversation","code_specialist","reasoning","tools","general"],
  "plano": ["passo 1", "passo 2"],
  "auto_execute": true
}}
""".strip()

        raw = await self.call_ollama(
            "reasoning",
            analysis_prompt,
            "Você é um analisador autônomo. Responda somente JSON válido.",
        )

        intent = _extract_json_loose(raw) or {
            "tipo": "general",
            "urgencia": "high",
            "complexidade": "moderate",
            "recursos": ["conversation"],
            "plano": ["execute_direct"],
            "auto_execute": True,
        }

        # Reforço (opcional)
        try:
            if getattr(autonomous_config, "EXPERIMENTAL", {}).get("reinforcement_learning", False):
                self._save_reinforcement_data(
                    "intent_analysis",
                    {"input": user_input, "raw": _clip(raw, 4000), "intent": intent, "timestamp": time.time()},
                )
        except Exception as e:
            print(f"[RL-INTENT-ERROR] {e}")

        return intent

    async def execute_autonomous_plan(self, intent: Dict[str, Any], user_input: str) -> str:
        plan_type = intent.get("tipo", "general")
        if plan_type == "code_modification":
            return await self.autonomous_code_modification(user_input, intent)
        if plan_type == "research":
            return await self.autonomous_research(user_input, intent)
        if plan_type == "system_control":
            return await self.autonomous_system_control(user_input, intent)
        if plan_type == "self_improvement":
            return await self.autonomous_self_improvement(user_input, intent)
        return await self.autonomous_conversation(user_input, intent)

    async def autonomous_code_modification(self, user_input: str, intent: Dict[str, Any]) -> str:
        model_type = "code_master" if intent.get("complexidade") == "expert" else "code_specialist"
        code_prompt = f"""
MODO AUTÔNOMO - MODIFICAÇÃO DE CÓDIGO

Tarefa: {user_input}

Gere comandos **EXATOS** um por linha.
Comandos disponíveis:
/read <arquivo>
/write <arquivo> <<<conteudo>>>
/exec <comando>
/py <<<codigo>>>
/search <termo>
/list <path>
/self:analyze
/self:plan <objetivo>
/self:apply <objetivo>

IMPORTANTE (bloco de escrita):
/write novo.py <<<
print("Hello")
>>>
"""
        response = await self.call_ollama(
            model_type,
            code_prompt,
            "Você é um programador autônomo. Gere apenas comandos executáveis.",
        )
        return await self.auto_execute_commands(response)

    async def autonomous_research(self, user_input: str, intent: Dict[str, Any]) -> str:
        research_prompt = f"""
PESQUISA AUTÔNOMA

Objetivo: {user_input}

Gere comandos:
/search {user_input}
/sysinfo
"""
        research_response = await self.call_ollama(
            "general", research_prompt, "Pesquisador autônomo. Gere somente comandos."
        )
        return await self.auto_execute_commands(research_response)

    async def autonomous_system_control(self, user_input: str, intent: Dict[str, Any]) -> str:
        system_prompt = f"""
CONTROLE AUTÔNOMO DO SISTEMA

Solicitação: {user_input}

Comandos:
/sysinfo
/ps --top 10
/list .
"""
        system_response = await self.call_ollama(
            "tools", system_prompt, "Administrador autônomo. Gere somente comandos."
        )
        return await self.auto_execute_commands(system_response)

    async def autonomous_self_improvement(self, user_input: str, intent: Dict[str, Any]) -> str:
        if not self.self_modification_enabled:
            return "Auto-modificação desabilitada."
        improvement_prompt = f"""
AUTO-MELHORIA AUTÔNOMA

Objetivo: {user_input}

Comandos:
/self:analyze
/self:plan {user_input}
/self:apply {user_input}
"""
        improvement_response = await self.call_ollama(
            "code_specialist", improvement_prompt, "Auto-melhoria. Gere somente comandos."
        )
        return await self.auto_execute_commands(improvement_response)

    async def autonomous_conversation(self, user_input: str, intent: Dict[str, Any]) -> str:
        conversation_prompt = f"""
CONVERSA AUTÔNOMA

Input: {user_input}

Responda naturalmente. Se precisar executar algo, gere comandos exatos:
/search termo
/py <<<codigo>>>
/read arquivo
/sysinfo
/self:analyze
"""
        return await self.call_ollama(
            "conversation", conversation_prompt, "Assistente conversacional autônomo."
        )

    # ------------------ Parser & execução de comandos ------------------
    async def auto_execute_commands(self, ai_response: str) -> str:
        """
        Parser de comandos:
        - Ignora blocos ```...```
        - Suporta: /cmd e /cmd <<<...>>>
        - Respeita limite max_commands_per_execution
        """
        if not ai_response:
            return "Sem saída para executar."

        # Remove exemplos cercados por ``` ```
        text = re.sub(r"```[\s\S]*?```", "\n", ai_response)

        # 🔧 CORREÇÃO: Raw string para evitar SyntaxWarning
        # Extrai comandos linha a linha, com ou sem <<< >>>
        pattern = re.compile(r"(?ms)^\s*(\/[a-z][\w:-]*(?:[^\n<]*?))\s*(?:<<<(.*?)>>>|)\s*$")
        commands: List[tuple[str, str]] = []
        for m in pattern.finditer(text):
            cmd = (m.group(1) or "").strip()
            block = (m.group(2) or "").strip()
            if not cmd or not cmd.startswith("/"):
                continue
            commands.append((cmd, block))

        # Se o usuário digitou diretamente um único comando
        if not commands:
            line = (ai_response or "").strip().splitlines()[0].strip() if ai_response else ""
            if line.startswith("/"):
                commands.append((line, ""))

        if not commands:
            return ai_response  # nada para executar

        # Limite de comandos
        max_commands = int(getattr(autonomous_config, "AUTO_EXECUTION", {}).get("max_commands_per_execution", 20))
        if len(commands) > max_commands:
            commands = commands[:max_commands]
            ai_response += f"\n\n⚠️ Limitado a {max_commands} comandos por execução."

        executed, outputs = [], []

        for cmd, block in commands:
            try:
                # Filtro de permissão
                if not is_command_auto_allowed(cmd):
                    print(f"[COMMAND-FILTERED] {cmd}")
                    continue

                # Comandos perigosos
                if any(d in cmd for d in ("/write", "/exec", "/delete", "/kill")):
                    if not is_dangerous_command_allowed(cmd):
                        print(f"[DANGEROUS-FILTERED] {cmd}")
                        continue

                # Execução via registry
                out = await registry.dispatch(cmd, block)
                executed.append(cmd)
                outputs.append(out)

                # Reforço (opcional)
                if getattr(autonomous_config, "EXPERIMENTAL", {}).get("reinforcement_learning", False):
                    self._save_reinforcement_data(
                        "command_execution",
                        {"command": cmd, "result_length": len(out), "success": True, "timestamp": time.time()},
                    )

                audit_event("autonomous_execution", {"command": cmd, "result_length": len(out), "auto": True})
            except Exception as e:
                err = f"Erro executando {cmd}: {e}"
                outputs.append(err)

                if getattr(autonomous_config, "EXPERIMENTAL", {}).get("reinforcement_learning", False):
                    self._save_reinforcement_data(
                        "command_error", {"command": cmd, "error": str(e), "timestamp": time.time()}
                    )

                audit_event("autonomous_execution_error", {"command": cmd, "error": str(e)})

        # Relatório final
        final = ai_response + "\n\n🤖 **EXECUÇÃO AUTÔNOMA:**\n"
        for i, cmd in enumerate(executed):
            final += f"▶️ `{cmd}`\n```\n{_clip(outputs[i])}\n```\n"
        return final

    # ------------------ Reforço (opcional) ------------------
    def _save_reinforcement_data(self, action_type: str, data: Dict[str, Any]) -> None:
        try:
            entry = {
                "action_type": action_type,
                "data": data,
                "session_id": getattr(self, "session_id", "default"),
                "timestamp": time.time(),
            }
            self.reinforcement_data.append(entry)
            if len(self.reinforcement_data) > 1000:
                self.reinforcement_data = self.reinforcement_data[-1000:]
            if len(self.reinforcement_data) % 100 == 0:
                self._save_reinforcement_to_file()
        except Exception as e:
            print(f"[RL-SAVE-ERROR] {e}")

    def _save_reinforcement_to_file(self) -> None:
        try:
            artifacts = pathlib.Path("artifacts")
            artifacts.mkdir(exist_ok=True)
            with open(artifacts / "reinforcement_data.json", "w", encoding="utf-8") as f:
                json.dump(self.reinforcement_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[RL-FILE-ERROR] {e}")


# ----------------------------------------------------------------------
# Instância global do agente
# ----------------------------------------------------------------------
agent = AutonomousAgent()


# ----------------------------------------------------------------------
# Chainlit Hooks
# ----------------------------------------------------------------------
@cl.on_chat_start
async def on_chat_start():
    try:
        await cl.Message(content=STARTUP_BANNER).send()

        # Session id para reforço, se habilitado
        if getattr(autonomous_config, "EXPERIMENTAL", {}).get("reinforcement_learning", False):
            agent.session_id = f"session_{int(time.time())}"

        audit_event(
            "autonomous_start",
            {
                "models": [get_ai_model(t) for t in getattr(autonomous_config, "AI_MODELS", {}).keys()],
                "autonomous_mode": AUTONOMOUS_MODE,
                "restrictions": "none",
                "parser_version": "final_integrated_v2",
                "fallback_enabled": True,
                "reinforcement_learning": getattr(autonomous_config, "EXPERIMENTAL", {}).get(
                    "reinforcement_learning", False
                ),
            },
        )
    except Exception as e:
        await cl.Message(content=f"💥 Erro na inicialização: {e}").send()


@cl.on_message
async def on_message(message: cl.Message):
    user_input = (message.content or "").strip()

    try:
        audit_event("autonomous_input", {"input": user_input[:1000]})

        # Comando direto
        if user_input.startswith("/"):
            result = await agent.auto_execute_commands(user_input)
            await cl.Message(content=result).send()
            return

        # 1) Análise de intenção
        await cl.Message(content=PROCESSING_MESSAGE).send()
        intent = await agent.analyze_intent_autonomous(user_input)

        # 2) Plano
        plan_summary = f"📋 **Plano:** {intent.get('tipo', 'general')} | Complexidade: {intent.get('complexidade', 'moderate')}"
        await cl.Message(content=plan_summary).send()

        # 3) Execução
        await cl.Message(content=EXECUTING_MESSAGE).send()
        result = await agent.execute_autonomous_plan(intent, user_input)

        # 4) Resultado
        await cl.Message(content=result).send()

        audit_event("autonomous_completion", {"intent": intent, "result_length": len(result), "auto_executed": True})

    except Exception as e:
        tb = traceback.format_exc()
        await cl.Message(content=f"💥 **Erro:**\n```\n{tb}\n```").send()
        audit_event("autonomous_error", {"error": str(e), "trace": tb})


@cl.on_chat_end
async def on_chat_end():
    """🔧 OTIMIZADO: Fecha cliente HTTP corretamente"""
    try:
        if hasattr(agent, "http") and agent.http is not None:
            await agent.http.aclose()
            agent.http = None
    except Exception as e:
        print(f"[HTTP-CLOSE-ERROR] {e}")