# -*- coding: utf-8 -*-
"""
Expert Router.

Este módulo define a lógica para um "meta-expert" ou roteador, que
seleciona o subconjunto apropriado de experts a serem consultados com base
na consulta do usuário.
"""
import logging
from typing import List, Dict

from pydantic import BaseModel, Field

from api.llm_client import OllamaClient, OllamaError
from api.experts.base import ExpertDefinition

logger = logging.getLogger(__name__)

# Modelo rápido e pequeno, ideal para tarefas de roteamento/classificação.
ROUTER_MODEL = "llama3:8b-instruct-q4_K_M"
ROUTER_TIMEOUT = 15

class RouterDecision(BaseModel):
    """Schema para a decisão do roteador."""
    experts_to_consult: List[str] = Field(..., description="A lista de nomes dos experts que devem ser consultados.")

ROUTER_PROMPT_TEMPLATE = """
Você é o Roteador de Análise de um comitê de experts em investimentos. Sua única tarefa é ler a consulta de um usuário e, com base em uma lista de experts disponíveis, decidir quais deles são relevantes para a consulta.

**REGRAS ESTRITAS:**
1.  **Formato de Saída:** Sua resposta DEVE ser um único objeto JSON, sem nenhum outro texto.
2.  **Schema Obrigatório:** O JSON deve seguir EXATAMENTE o schema `{"experts_to_consult": ["expert_name_1", "expert_name_2"]}`.
3.  **Foco na Relevância:** Selecione apenas os experts cuja especialidade está diretamente relacionada à consulta.
4.  **Sempre Inclua Risco e Macro:** Os experts 'risk' e 'macro' fornecem contexto essencial. SEMPRE inclua-os na sua decisão, além dos outros que você julgar relevantes.
5.  **Consulta Ambigua:** Se a consulta for muito geral ou ambígua (ex: "analise a apple"), selecione os experts primários de análise ('technical', 'fundamental'). Se o ticker parecer ser de cripto, inclua o 'crypto'.

**EXPERTS DISPONÍVEIS:**
{expert_descriptions}

**TAREFA:**
Leia a consulta do usuário e o ticker. Decida quais experts devem ser consultados.

**Consulta do Usuário:** "{query}"
**Ticker:** "{ticker}"

**EXEMPLO DE SAÍDA JSON VÁLIDA:**
```json
{{
  "experts_to_consult": ["technical", "risk", "macro"]
}}
```

Agora, gere sua decisão de roteamento em formato JSON.
"""

class ExpertRouter:
    """
    Usa um LLM para rotear uma consulta para os experts mais relevantes.
    """
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_client = OllamaClient(host=ollama_host)

    def _get_expert_descriptions(self, experts: Dict[str, ExpertDefinition]) -> str:
        """Cria uma string formatada com as descrições dos experts."""
        descriptions = []
        for name, expert_def in experts.items():
            # Extrai a primeira linha da docstring do expert como descrição
            docstring = expert_def.response_model.__doc__ or "Nenhuma descrição."
            description = docstring.strip().split('\n')[0]
            descriptions.append(f"- **{name}**: {description}")
        return "\n".join(descriptions)

    async def route_query(self, query: str, ticker: str, available_experts: Dict[str, ExpertDefinition]) -> List[str]:
        """
        Determina qual subconjunto de experts deve ser consultado.
        """
        logger.info(f"Roteando consulta para o ticker '{ticker}'...")

        expert_descriptions = self._get_expert_descriptions(available_experts)
        prompt = ROUTER_PROMPT_TEMPLATE.format(
            query=query,
            ticker=ticker,
            expert_descriptions=expert_descriptions
        )

        try:
            llm_response_json = await self.ollama_client.generate_ollama(
                model=ROUTER_MODEL,
                prompt=prompt,
                timeout=ROUTER_TIMEOUT,
            )

            decision = RouterDecision.model_validate(llm_response_json)

            # Garante que a lista contém apenas experts que realmente existem
            valid_experts = [expert for expert in decision.experts_to_consult if expert in available_experts]

            logger.info(f"Roteador decidiu consultar os seguintes experts: {valid_experts}")
            return valid_experts

        except (OllamaError, Exception) as e:
            logger.error(f"Falha no roteador de experts: {e}. Usando fallback.", exc_info=True)
            # Fallback: se o roteador falhar, consulte os experts primários como padrão
            return ["technical", "fundamental", "risk", "macro", "sentiment", "crypto"]

    async def close_connections(self):
        """Fecha as conexões do cliente Ollama."""
        await self.ollama_client.close()
