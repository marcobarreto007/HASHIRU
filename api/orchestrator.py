# -*- coding: utf-8 -*-
"""
Analysis Orchestrator (Dynamic Loading).

Este módulo orquestra as chamadas para os diferentes experts, descobrindo-os
e carregando-os dinamicamente a partir do diretório de experts.
"""

import logging
import asyncio
import os
import importlib
from typing import Dict, Any, Type, Union, List

from pydantic import BaseModel
from api.llm_client import OllamaClient, OllamaError
from api.experts.base import ExpertDefinition
from api.router import ExpertRouter

# Configurar um logger para este módulo
logger = logging.getLogger(__name__)

# TODO: Mover para um arquivo de configuração
DEFAULT_TIMEOUT = 90

class AnalysisOrchestrator:
    """
    Orquestra a análise financeira, descobrindo e coordenando dinamicamente
    um "Comitê de Experts" LLM.
    """

    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """
        Inicializa o orquestrador e carrega os experts dinamicamente.
        """
        self.ollama_client = OllamaClient(host=ollama_host)
        self.router = ExpertRouter(ollama_host=ollama_host)
        self.experts: Dict[str, ExpertDefinition] = self._load_experts_from_directory()
        logger.info("Orquestrador de Análise Dinâmico inicializado com %d experts.", len(self.experts))

    def _load_experts_from_directory(self) -> Dict[str, ExpertDefinition]:
        """
        Descobre e carrega dinamicamente os experts do diretório 'api/experts'.
        """
        experts_dir = os.path.dirname(__file__) + "/experts"
        expert_definitions = {}

        for filename in os.listdir(experts_dir):
            if filename.endswith(".py") and not filename.startswith("__") and filename != "base.py":
                module_name = f"api.experts.{filename[:-3]}"
                try:
                    module = importlib.import_module(module_name)
                    if hasattr(module, "expert_definition") and isinstance(module.expert_definition, ExpertDefinition):
                        expert_def = module.expert_definition
                        expert_definitions[expert_def.name] = expert_def
                        logger.info(f"Expert '{expert_def.name}' carregado dinamicamente de '{filename}'.")
                    else:
                        logger.warning(f"Módulo '{module_name}' não possui uma 'expert_definition' válida.")
                except Exception as e:
                    logger.error(f"Falha ao carregar o expert do módulo '{module_name}': {e}", exc_info=True)

        return expert_definitions

    async def _run_single_expert(self, expert: ExpertDefinition, query: str, ticker: str) -> Union[BaseModel, None]:
        """
        Executa a análise para um único expert e lida com erros de forma isolada.
        """
        logger.info(f"Iniciando análise do expert '{expert.name}' para o ticker '{ticker}'.")
        prompt = expert.prompt_template.format(ticker=ticker, query=query)

        try:
            llm_response_json = await self.ollama_client.generate_ollama(
                model=expert.model_name, # Usa o modelo definido pelo expert
                prompt=prompt,
                timeout=DEFAULT_TIMEOUT,
            )

            validated_response = expert.response_model.model_validate(llm_response_json)
            logger.info(f"Análise do expert '{expert.name}' para '{ticker}' validada com sucesso.")
            return validated_response

        except (OllamaError, Exception) as e:
            logger.error(f"Falha no expert '{expert.name}' para '{ticker}': {e}", exc_info=True)
            return None

    async def run_investment_committee(self, query: str, ticker: str) -> Dict[str, BaseModel | None]:
        """
        Executa o comitê de experts em paralelo após consultar o roteador.
        """
        logger.info(f"Iniciando comitê de investimentos para o ticker '{ticker}'.")

        # 1. Consultar o roteador para decidir quais experts usar
        experts_to_consult = await self.router.route_query(query, ticker, self.experts)

        if not experts_to_consult:
            logger.warning("O roteador não selecionou nenhum expert. Nenhum comitê será executado.")
            return {}

        # 2. Criar e executar tarefas apenas para os experts selecionados
        tasks = []
        selected_expert_definitions = []
        for expert_name in experts_to_consult:
            if expert_name in self.experts:
                expert_def = self.experts[expert_name]
                tasks.append(self._run_single_expert(expert_def, query, ticker))
                selected_expert_definitions.append(expert_def)

        expert_results_list = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. Mapear resultados de volta para os nomes dos experts
        final_analysis = {}
        for i, result in enumerate(expert_results_list):
            expert_name = selected_expert_definitions[i].name
            if isinstance(result, Exception):
                logger.error(f"Exceção capturada para o expert '{expert_name}': {result}")
                final_analysis[expert_name] = None
            else:
                final_analysis[expert_name] = result

        logger.info(f"Comitê de investimentos para '{ticker}' finalizado. Experts consultados: {experts_to_consult}")
        return final_analysis

    async def close_connections(self):
        """Fecha as conexões do cliente Ollama."""
        await self.ollama_client.close()
        logger.info("Conexões do orquestrador fechadas.")

    def aggregate_committee_results(self, expert_analyses: Dict[str, BaseModel | None], ticker: str, query: str) -> "AggregateDecision":
        """
        Agrega os resultados do comitê de experts usando um sistema de votação
        ponderado pela confiança e com lógica de resolução de conflitos.
        """
        from api.decision_models import AggregateDecision

        weighted_votes = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        summaries = []
        total_confidence_for_avg = []

        # 1. Acumular Votos Ponderados dos Experts Primários
        primary_experts = ["technical", "fundamental", "crypto"]
        for expert_name in primary_experts:
            result = expert_analyses.get(expert_name)
            if not result or not hasattr(result, 'signal') or not hasattr(result, 'confidence'):
                continue

            # O expert de cripto só vota se o ativo for de fato cripto
            if expert_name == "crypto" and not getattr(result, 'is_crypto', False):
                continue

            signal = str(getattr(result, 'signal', 'NO_TRADE')).upper()
            if signal in weighted_votes:
                confidence = getattr(result, 'confidence', 0.5)
                weighted_votes[signal] += confidence
                total_confidence_for_avg.append(confidence)
                summaries.append(f"- **{expert_name.capitalize()} ({signal}, Conf: {confidence:.0%})**: {getattr(result, 'summary', 'N/A')}")

        # 2. Determinar o Sinal Vencedor com Base nos Pesos
        if not any(weighted_votes.values()):
            winning_signal = "NO_TRADE"
            summary_of_reasoning = "Nenhum expert primário conseguiu fornecer um sinal claro de negociação."
        else:
            # Lógica de Resolução de Conflito
            buy_score = weighted_votes.get("BUY", 0.0)
            sell_score = weighted_votes.get("SELL", 0.0)

            # Se os sinais de compra e venda são fortes e próximos, é um conflito -> HOLD
            if buy_score > 0.5 and sell_score > 0.5 and abs(buy_score - sell_score) < 0.3:
                winning_signal = "HOLD"
                summaries.append("- **Conflito de Sinais**: Sinais de compra e venda fortes e conflitantes foram identificados. Recomendação rebaixada para MANTER por segurança.")
            else:
                winning_signal = max(weighted_votes, key=weighted_votes.get)

            # 3. Aplicar Modificadores de Risco e Macro
            risk_analysis = expert_analyses.get("risk")
            if risk_analysis and hasattr(risk_analysis, 'overall_risk_level') and risk_analysis.overall_risk_level == "HIGH":
                if winning_signal == "BUY":
                    winning_signal = "HOLD"
                    summaries.append("- **Modificador de Risco**: O alto risco identificado rebaixou a recomendação de COMPRA para MANTER.")

            macro_analysis = expert_analyses.get("macro")
            if macro_analysis and hasattr(macro_analysis, 'overall_impact') and macro_analysis.overall_impact == "NEGATIVE_IMPACT":
                if winning_signal == "BUY":
                    winning_signal = "HOLD"
                    summaries.append("- **Modificador Macro**: O cenário macroeconômico negativo rebaixou a recomendação de COMPRA para MANTER.")

            summary_of_reasoning = "A decisão final foi baseada na seguinte análise consolidada:\n" + "\n".join(summaries)

        # 4. Calcular Confiança Final
        total_score = sum(weighted_votes.values())
        if total_score > 0:
            # A confiança final é a proporção do peso do sinal vencedor sobre o total de pesos
            final_confidence = weighted_votes[winning_signal] / total_score if winning_signal in weighted_votes else 0.0
        else:
            final_confidence = 0.0

        return AggregateDecision(
            final_signal=winning_signal,
            confidence=round(final_confidence, 2),
            summary_of_reasoning=summary_of_reasoning,
            expert_analysis={k: v.model_dump() if v else None for k, v in expert_analyses.items()},
            ticker=ticker,
            request_query=query,
        )
