# -*- coding: utf-8 -*-
"""
Analysis Orchestrator.

Este módulo é responsável por orquestrar as chamadas para os diferentes
experts (LLMs) e agregar suas respostas para formar uma decisão final.
"""

import logging
import asyncio
from typing import Dict, Any, Type, Union

from pydantic import BaseModel, ValidationError

from api.llm_client import OllamaClient, OllamaError

# Importar todos os schemas e templates de prompt dos experts
from api.experts.technical_analyst import TECHNICAL_ANALYSIS_PROMPT_TEMPLATE, TechnicalAnalysisSignal
from api.experts.fundamental_analyst import FUNDAMENTAL_ANALYSIS_PROMPT_TEMPLATE, FundamentalAnalysisSignal
from api.experts.macro_analyst import MACRO_ANALYSIS_PROMPT_TEMPLATE, MacroAnalysisSignal
from api.experts.risk_analyst import RISK_ANALYSIS_PROMPT_TEMPLATE, RiskAnalysisSignal
from api.experts.sentiment_analyst import SENTIMENT_ANALYSIS_PROMPT_TEMPLATE, SentimentAnalysisSignal
from api.experts.crypto_analyst import CRYPTO_ANALYSIS_PROMPT_TEMPLATE, CryptoAnalysisSignal

# Configurar um logger para este módulo
logger = logging.getLogger(__name__)

# TODO: Mover para um arquivo de configuração
DEFAULT_MODEL = "llama3"
DEFAULT_TIMEOUT = 90

# Type alias para os possíveis modelos de Pydantic que os experts podem retornar
ExpertSignal = Union[
    TechnicalAnalysisSignal,
    FundamentalAnalysisSignal,
    MacroAnalysisSignal,
    RiskAnalysisSignal,
    SentimentAnalysisSignal,
    CryptoAnalysisSignal,
]

class AnalysisOrchestrator:
    """
    Orquestra a análise financeira, coordenando chamadas para o "Comitê de Experts" LLM.
    """

    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """
        Inicializa o orquestrador.
        """
        self.ollama_client = OllamaClient(host=ollama_host)
        self.experts = {
            "technical": (TECHNICAL_ANALYSIS_PROMPT_TEMPLATE, TechnicalAnalysisSignal),
            "fundamental": (FUNDAMENTAL_ANALYSIS_PROMPT_TEMPLATE, FundamentalAnalysisSignal),
            "macro": (MACRO_ANALYSIS_PROMPT_TEMPLATE, MacroAnalysisSignal),
            "risk": (RISK_ANALYSIS_PROMPT_TEMPLATE, RiskAnalysisSignal),
            "sentiment": (SENTIMENT_ANALYSIS_PROMPT_TEMPLATE, SentimentAnalysisSignal),
            "crypto": (CRYPTO_ANALYSIS_PROMPT_TEMPLATE, CryptoAnalysisSignal),
        }
        logger.info("Orquestrador de Análise do Comitê inicializado com %d experts.", len(self.experts))

    async def _run_single_expert(
        self, expert_name: str, prompt_template: str, response_model: Type[BaseModel], query: str, ticker: str
    ) -> ExpertSignal | None:
        """
        Executa a análise para um único expert e lida com erros de forma isolada.
        """
        logger.info(f"Iniciando análise do expert '{expert_name}' para o ticker '{ticker}'.")
        prompt = prompt_template.format(ticker=ticker, query=query)

        try:
            llm_response_json = await self.ollama_client.generate_ollama(
                model=DEFAULT_MODEL,
                prompt=prompt,
                timeout=DEFAULT_TIMEOUT,
            )

            validated_response = response_model.model_validate(llm_response_json)
            logger.info(f"Análise do expert '{expert_name}' para '{ticker}' validada com sucesso.")
            return validated_response

        except (OllamaError, ValidationError) as e:
            logger.error(f"Falha no expert '{expert_name}' para '{ticker}': {e}")
            return None # Retorna None para indicar falha neste expert específico
        except Exception as e:
            logger.exception(f"Erro inesperado no expert '{expert_name}' para '{ticker}'.")
            return None

    async def run_investment_committee(self, query: str, ticker: str) -> Dict[str, ExpertSignal | None]:
        """
        Executa o comitê de experts em paralelo.

        Cria tarefas para cada expert e as executa concorrentemente usando asyncio.gather.
        Se um expert falhar, os outros não são afetados.

        Args:
            query (str): A consulta original do usuário.
            ticker (str): O ticker do ativo a ser analisado.

        Returns:
            Um dicionário com os resultados de cada expert. O valor será None se um expert falhar.
        """
        logger.info(f"Iniciando comitê de investimentos para o ticker '{ticker}'.")

        tasks = []
        for name, (template, model) in self.experts.items():
            task = self._run_single_expert(
                expert_name=name,
                prompt_template=template,
                response_model=model,
                query=query,
                ticker=ticker,
            )
            tasks.append(task)

        # Executa todas as análises em paralelo e coleta os resultados
        expert_results = await asyncio.gather(*tasks, return_exceptions=True)

        final_analysis = {}
        for i, expert_name in enumerate(self.experts.keys()):
            result = expert_results[i]
            if isinstance(result, Exception):
                logger.error(f"Exceção capturada pelo asyncio.gather para o expert '{expert_name}': {result}")
                final_analysis[expert_name] = None
            else:
                final_analysis[expert_name] = result

        logger.info(f"Comitê de investimentos para '{ticker}' finalizado.")
        return final_analysis


    async def close_connections(self):
        """Fecha as conexões do cliente Ollama."""
        await self.ollama_client.close()
        logger.info("Conexões do orquestrador fechadas.")

    def aggregate_committee_results(self, expert_analyses: Dict[str, ExpertSignal | None], ticker: str, query: str) -> "AggregateDecision":
        """
        Agrega os resultados do comitê de experts em uma única decisão acionável.

        A lógica de agregação inicial é baseada em uma contagem de votos, com
        modificadores de risco e macro.
        """
        from api.decision_models import AggregateDecision
        from collections import Counter

        votes = []
        summaries = []
        confidences = []

        # Coletar votos e dados dos experts de sinal primário
        primary_signals = ["technical", "fundamental", "crypto"]
        for expert_name in primary_signals:
            result = expert_analyses.get(expert_name)
            if result:
                # O expert de cripto só vota se o ativo for cripto
                if expert_name == "crypto" and getattr(result, 'is_crypto', False):
                    if result.signal not in ["NO_TRADE", "NOT_APPLICABLE"]:
                        votes.append(result.signal)
                        confidences.append(result.confidence)
                        summaries.append(f"- **{expert_name.capitalize()}**: {result.summary}")
                elif expert_name != "crypto":
                    if result.signal != "NO_TRADE":
                        votes.append(result.signal)
                        confidences.append(result.confidence)
                        summaries.append(f"- **{expert_name.capitalize()}**: {result.summary}")

        # Analisar fatores de modificação (Risco e Macro)
        risk_analysis = expert_analyses.get("risk")
        macro_analysis = expert_analyses.get("macro")

        # Lógica de Votação
        if not votes:
            final_signal = "NO_TRADE"
            summary_of_reasoning = "Nenhum expert primário conseguiu fornecer um sinal claro de negociação."
        else:
            vote_counts = Counter(votes)
            # O sinal vencedor é o mais comum. Em caso de empate, a lógica pode ser refinada.
            # Por simplicidade, pega o mais comum. Se houver empate, a ordem é arbitrária.
            winner_signal = vote_counts.most_common(1)[0][0]
            final_signal = winner_signal

            # Modificadores
            if risk_analysis and risk_analysis.overall_risk_level == "HIGH":
                if final_signal == "BUY":
                    final_signal = "HOLD" # Rebaixa Compra para Manter se o risco for alto
                    summaries.append("- **Modificador de Risco**: O alto risco identificado rebaixou a recomendação de COMPRA para MANTER.")

            if macro_analysis and macro_analysis.overall_impact == "NEGATIVE_IMPACT":
                 if final_signal == "BUY":
                    final_signal = "HOLD" # Rebaixa Compra para Manter se o macro for negativo
                    summaries.append("- **Modificador Macro**: O cenário macroeconômico negativo rebaixou a recomendação de COMPRA para MANTER.")

            summary_of_reasoning = "A decisão final foi baseada na seguinte análise consolidada:\n" + "\n".join(summaries)


        # Calcular confiança final (média simples por enquanto)
        final_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        return AggregateDecision(
            final_signal=final_signal,
            confidence=round(final_confidence, 2),
            summary_of_reasoning=summary_of_reasoning,
            expert_analysis={k: v.model_dump() if v else None for k, v in expert_analyses.items()},
            ticker=ticker,
            request_query=query,
        )
