# -*- coding: utf-8 -*-
"""
Expert: Analista Fundamentalista.

Este módulo define a lógica e os prompts para o expert focado em
análise fundamentalista de ativos financeiros.
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional

class SignalEnum(str, Enum):
    """Enumeração dos possíveis sinais de negociação."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NO_TRADE = "NO_TRADE"

class FundamentalMetric(BaseModel):
    """Schema para uma métrica fundamentalista específica."""
    name: str = Field(..., description="Nome da métrica (ex: 'P/L', 'Crescimento da Receita Anual').")
    value: str = Field(..., description="Valor da métrica.")
    analysis: str = Field(..., description="Breve análise da métrica (ex: 'Abaixo da média do setor', 'Sólido crescimento de dois dígitos').")

class FundamentalAnalysisSignal(BaseModel):
    """
    Schema para a decisão final da análise fundamentalista.
    Este é o formato JSON que o LLM deve retornar.
    """
    signal: SignalEnum = Field(..., description="O sinal de negociação final com base nos fundamentos.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nível de confiança no sinal, de 0.0 a 1.0.")
    summary: str = Field(..., description="Um resumo conciso da saúde financeira da empresa e da lógica por trás da decisão.")
    key_metrics: List[FundamentalMetric] = Field(..., description="Uma lista das principais métricas fundamentalistas que suportam a decisão.")
    valuation: str = Field(..., description="Análise de valuation (ex: 'Subvalorizado', 'Justo', 'Sobrevalorizado').")

# Prompt para o Expert de Análise Fundamentalista
FUNDAMENTAL_ANALYSIS_PROMPT_TEMPLATE = """
Você é um Analista de Equity Research Sênior, especializado em análise fundamentalista "bottom-up". Sua tarefa é avaliar a saúde financeira e o valor intrínseco de uma empresa para fornecer uma recomendação de investimento de longo prazo.

**REGRAS ESTRITAS:**
1.  **Formato de Saída:** Sua resposta DEVE ser um único objeto JSON, sem nenhum outro texto.
2.  **Schema Obrigatório:** O JSON deve seguir EXATAMENTE o schema abaixo.
3.  **Análise Focada:** Analise a empresa por trás do ticker `{ticker}`. Avalie seus balanços, receita, lucro, dívida e vantagens competitivas.
4.  **Sem Conclusão = NO_TRADE:** Se os dados forem insuficientes ou contraditórios, sua recomendação DEVE ser "NO_TRADE".
5.  **Foco no Longo Prazo:** Sua análise não deve considerar movimentos de preço de curto prazo.

**TAREFA:**
Realize uma análise fundamentalista para o ticker **{ticker}**. Com base na sua análise, gere um objeto JSON com sua recomendação.

**SCHEMA JSON DE SAÍDA OBRIGATÓRIO:**
```json
{{
  "signal": "BUY" | "SELL" | "HOLD" | "NO_TRADE",
  "confidence": float (0.0 a 1.0),
  "summary": "string",
  "key_metrics": [
    {{
      "name": "string",
      "value": "string",
      "analysis": "string"
    }}
  ],
  "valuation": "Subvalorizado" | "Justo" | "Sobrevalorizado"
}}
```

**EXEMPLO DE SAÍDA JSON VÁLIDA:**
```json
{{
  "signal": "BUY",
  "confidence": 0.8,
  "summary": "A empresa demonstra um crescimento de receita consistente, margens de lucro em expansão e um balanço sólido com baixo endividamento. O fosso competitivo parece durável.",
  "key_metrics": [
    {{
      "name": "P/L (TTM)",
      "value": "18.5x",
      "analysis": "Abaixo da média histórica da empresa (25x) e do setor (22x), sugerindo subvalorização."
    }},
    {{
      "name": "Crescimento da Receita (YoY)",
      "value": "15%",
      "analysis": "Crescimento robusto impulsionado pela expansão em novos mercados."
    }},
    {{
      "name": "Dívida/Patrimônio Líquido",
      "value": "0.2",
      "analysis": "Nível de alavancagem muito baixo, indicando baixo risco financeiro."
    }}
  ],
  "valuation": "Subvalorizado"
}}
```

Agora, execute a análise para o ticker `{ticker}` com base na seguinte consulta do usuário: "{query}"
"""
