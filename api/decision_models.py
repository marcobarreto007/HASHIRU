# -*- coding: utf-8 -*-
"""
Pydantic Models for Aggregated Decisions.

Este arquivo define os modelos de dados para as saídas consolidadas da API,
após a agregação das análises dos diversos experts.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List

# Importar os enums e schemas dos experts para referência
from .experts.technical_analyst import SignalEnum, TechnicalAnalysisSignal
from .experts.fundamental_analyst import FundamentalAnalysisSignal
from .experts.macro_analyst import MacroAnalysisSignal, MacroSignalEnum
from .experts.risk_analyst import RiskAnalysisSignal, RiskLevelEnum
from .experts.sentiment_analyst import SentimentAnalysisSignal, SentimentEnum as SentimentSignalEnum
from .experts.crypto_analyst import CryptoAnalysisSignal, CryptoSignalEnum

class AggregateDecision(BaseModel):
    """
    Schema para a decisão de investimento final e agregada do comitê.
    Este é o principal objeto de resposta do endpoint /api/ask.
    """
    # A Decisão Final
    final_signal: SignalEnum = Field(..., description="A recomendação de negociação final, agregada de todos os experts.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="A confiança combinada na decisão final.")

    # Rationale e Resumo
    summary_of_reasoning: str = Field(..., description="Um resumo executivo que explica a lógica por trás da decisão final, considerando as visões convergentes e divergentes dos experts.")

    # Análises Individuais dos Experts
    expert_analysis: Dict[str, Any] = Field(..., description="Um dicionário contendo a análise detalhada de cada expert que contribuiu para a decisão.")

    # Metadados da Análise
    ticker: str = Field(..., description="O ticker do ativo analisado.")
    request_query: str = Field(..., description="A consulta original do usuário.")

class HealthStatus(BaseModel):
    """
    Schema para a resposta do endpoint /api/health.
    """
    status: str = Field(..., description="Status geral da API ('healthy' ou 'degraded').")
    version: str = Field(..., description="Versão da API.")
    cache_backend: str = Field(..., description="Backend de cache em uso ('redis' ou 'memory').")
    dependencies: Dict[str, str] = Field(..., description="Status detalhado das dependências críticas.")
