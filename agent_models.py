# main_agent.py
# -*- coding: utf-8 -*-
"""
HASHIRU 6.8 - ARQUITETURA FINAL ESTÁVEL

Esta versão finaliza a separação de responsabilidades, movendo os
modelos de dados para seu próprio arquivo e estabilizando a arquitetura.
"""
from __future__ import annotations
import traceback
import sys
import pathlib
import logging
import json

import chainlit as cl
import httpx

# ----------------------------------------------------------------------
# 1. CONFIGURAÇÃO INICIAL E DEPENDÊNCIAS
# ----------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")
logger = logging.getLogger("HASHIRU_AGENT")

ROOT_PATH = pathlib.Path(__file__).resolve().parent
if str(ROOT_PATH) not in sys.path:
    sys.path.insert(0, str(ROOT_PATH))

# --- Importações do Projeto ---
from autonomous_config import config, Config
from agent_tools import TOOL_REGISTRY, get_tools_description_for_llm
# >>> NOVO: Importa as estruturas de dados do seu próprio arquivo <<<
from agent_models import Task, ToolCall

# ----------------------------------------------------------------------
# 2. CLASSES DO AGENTE (Sem as definições de dataclass)
# ----------------------------------------------------------------------

class Planner:
    """Cria um plano de ação (uma lista de ToolCalls) para resolver a solicitação."""
    def __init__(self, config: Config, http_client: httpx.AsyncClient):
        self.config = config
        self.http_client = http_client
        self.system_prompt = (
            "Você é um planejador para um agente de IA. Sua tarefa é decompor a solicitação do usuário em uma sequência de passos, onde cada passo é uma chamada a uma ferramenta. "
            "As ferramentas disponíveis são:\n{tools}\n\n"
            "Responda APENAS com um objeto JSON contendo uma chave 'plan', que é uma lista de ações. "
            "Cada ação na lista deve ter 'tool_name' e 'tool_input'. Exemplo de resposta: "
            '{"plan": [{"tool_name": "read_file", "tool_input": {"file_path": "main.py"}}]}'
        )

    async def create_task_with_plan(self, user_input: str) -> Task:
        """Usa o LLM para criar uma Task completa com um plano de ferramentas."""
        model = self.config.get_model("reasoning")
        prompt = self.system_prompt.format(tools=get_tools_description_for_llm())
        
        try:
            response_json = await self._call_ollama(model, f"Crie um plano para: '{user_input}'", prompt)
            data = json.loads(response_json)
            plan_data = data.get("plan", [])
            plan = [ToolCall(**call) for call in plan_data]
            return Task("tool_based_plan", "Executar plano de ferramentas", user_input, plan)
        except (json.JSONDecodeError, httpx.RequestError, TypeError) as e:
            logger.error(f"Falha ao criar plano, tratando como conversa. Erro: {e}", exc_info=True)
            return Task("general_conversation", "Conversa geral", user_input, [])

    async def _call_ollama(self, model: str, prompt: str, system: str) -> str:
        payload = {"model": model, "prompt": prompt, "system": system, "stream": False, "format": "json"}
        r = await self.http_client.post(f"{self.config.ollama.base_url}/api/generate", json=payload)
        r.raise_for_status()
        return r.json().get("response", "{}")

class Executor:
    """Executa um plano de ToolCalls em sequência."""
    def __init__(self, config: Config):
        self.config = config

    async def execute_plan(self, plan: list[ToolCall]) -> str:
        """Itera sobre um plano e executa cada chamada de ferramenta."""
        if not plan:
            return "## ✅ Plano Concluído\nNenhuma ação foi planejada, pois a tarefa não exigia ferramentas."

        results = []
        for i, tool_call in enumerate(plan):
            async with cl.Step(name=f"Passo {i+1}: `{tool_call.tool_name}`") as step:
                step.input = str(tool_call.tool_input)
                
                tool = TOOL_REGISTRY.get(tool_call.tool_name)
                if not tool:
                    output = f"Erro: Ferramenta '{tool_call.tool_name}' não encontrada."
                else:
                    try:
                        output = tool.execute(tool_call.tool_input)
                    except Exception as e:
                        output = f"Erro ao executar a ferramenta '{tool.name}': {e}"
                
                step.output = output
                results.append(f"#### ✅ Passo {i+1}: `{tool.name}`\n**Resultado:**\n```\n{output}\n```")
        
        return "## 📝 Relatório Final de Execução\n\n" + "\n\n---\n\n".join(results)

class AgentSession:
    """Gerencia o ciclo de vida completo de uma interação."""
    def __init__(self, config: Config):
        self.config = config
        self.http_client = httpx.AsyncClient(timeout=config.ollama.timeout)
        self.planner = Planner(config, self.http_client)
        self.executor = Executor(config)

    async def handle_message(self, user_input: str):
        """Orquestra o fluxo de Planejar -> Executar."""
        await cl.Message(content=self.config.processing_message).send()
        
        task = await self.planner.create_task_with_plan(user_input)
        
        if not task.plan:
            plan_summary = "Não foi criado um plano de ferramentas. Tentando responder diretamente..."
            await cl.Message(content=plan_summary).send()
            # Fallback para uma conversa simples se o planejamento falhar
            # (Em uma versão futura, isso também poderia ser uma chamada ao LLM)
            response = "Desculpe, não consegui transformar sua solicitação em um plano de ação. Pode tentar ser mais específico ou pedir algo que use as ferramentas disponíveis?"
        else:
            plan_summary = "**Plano de Ação:**\n" + "\n".join([f"- Usar `{tc.tool_name}`" for tc in task.plan])
            await cl.Message(content=plan_summary).send()
            
            await cl.Message(content=self.config.executing_message).send()
            response = await self.executor.execute_plan(task.plan)
            
        await cl.Message(content=response).send()

    async def cleanup(self):
        await self.http_client.aclose()
        logger.info("Sessão do agente finalizada.")

# ----------------------------------------------------------------------
# 3. HOOKS DO CHAINLIT (A Camada de Interface)
# ----------------------------------------------------------------------
@cl.on_chat_start
async def on_chat_start():
    agent_session = AgentSession(config)
    cl.user_session.set("agent_session", agent_session)
    await cl.Message(content=config.startup_banner).send()

@cl.on_message
async def on_message(message: cl.Message):
    agent = cl.user_session.get("agent_session")
    user_input = (message.content or "").strip()
    if not user_input or not agent: return
    
    try:
        await agent.handle_message(user_input)
    except Exception:
        tb = traceback.format_exc()
        logger.error(f"Erro irrecuperável no fluxo principal:\n{tb}")
        await cl.Message(content=f"💥 **Erro Inesperado no Sistema:**\n```\n{tb}\n```").send()

@cl.on_chat_end
async def on_chat_end():
    if agent := cl.user_session.get("agent_session"):
        await agent.cleanup()