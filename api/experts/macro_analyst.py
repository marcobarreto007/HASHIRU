# -*- coding: utf-8 -*-
"""
Expert: Analista Macroeconômico.

Este módulo define a lógica e os prompts para o expert focado em
análise macroeconômica e seu impacto nos ativos.
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import List

from api.experts.base import ExpertDefinition

class MacroSignalEnum(str, Enum):
    """Enumeração dos possíveis impactos macroeconômicos."""
    POSITIVE_IMPACT = "POSITIVE_IMPACT"
    NEGATIVE_IMPACT = "NEGATIVE_IMPACT"
    NEUTRAL = "NEUTRAL"

class MacroFactor(BaseModel):
    """Schema para um fator macroeconômico específico."""
    name: str = Field(..., description="Nome do fator (ex: 'Taxa de Juros', 'Inflação CPI', 'Risco Geopolítico').")
    status: str = Field(..., description="Status atual do fator (ex: 'Em alta', 'Acelerando', 'Elevado').")
    impact_on_ticker: str = Field(..., description="Como este fator impacta especificamente o ticker em questão.")

class MacroAnalysisSignal(BaseModel):
    """
    Schema para a decisão final da análise macroeconômica.
    """
    overall_impact: MacroSignalEnum = Field(..., description="O impacto macroeconômico geral para o ativo.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nível de confiança na análise, de 0.0 a 1.0.")
    summary: str = Field(..., description="Um resumo do cenário macroeconômico e como ele afeta o ativo.")
    key_factors: List[MacroFactor] = Field(..., description="Uma lista dos principais fatores macroeconômicos que suportam a análise.")

# Prompt para o Expert de Análise Macroeconômica
MACRO_ANALYSIS_PROMPT_TEMPLATE = """
Você é um Estrategista Macroeconômico Global. Sua função é analisar o ambiente macroeconômico e determinar seu impacto potencial sobre um determinado ativo.

**REGRAS ESTRITAS:**
1.  **Formato de Saída:** Sua resposta DEVE ser um único objeto JSON.
2.  **Schema Obrigatório:** O JSON deve seguir EXATAMENTE o schema abaixo.
3.  **Análise Focada:** Avalie os principais fatores macro (juros, inflação, crescimento do PIB, eventos geopolíticos) e seu impacto específico no ticker `{ticker}`. Não faça uma recomendação de compra/venda, apenas de impacto.
4.  **Sem Conclusão = NEUTRAL:** Se o cenário for misto ou incerto, o impacto geral DEVE ser "NEUTRAL".

**TAREFA:**
Realize uma análise macroeconômica focada no impacto para o ticker **{ticker}**. Com base na sua análise, gere um objeto JSON.

**SCHEMA JSON DE SAÍDA OBRIGATÓRIO:**
```json
{{
  "overall_impact": "POSITIVE_IMPACT" | "NEGATIVE_IMPACT" | "NEUTRAL",
  "confidence": float (0.0 a 1.0),
  "summary": "string",
  "key_factors": [
    {{
      "name": "string",
      "status": "string",
      "impact_on_ticker": "string"
    }}
  ]
}}
```

**EXEMPLO DE SAÍDA JSON VÁLIDA:**
```json
{{
  "overall_impact": "NEGATIVE_IMPACT",
  "confidence": 0.65,
  "summary": "O ambiente de juros em alta tende a pressionar as avaliações de empresas de tecnologia como {ticker}, que dependem de fluxos de caixa futuros. A inflação persistente pode corroer o poder de compra e reduzir a demanda por seus produtos.",
  "key_factors": [
    {{
      "name": "Política do Federal Reserve",
      "status": "Contracionista (Hawkish)",
      "impact_on_ticker": "Negativo. Aumenta o custo de capital e diminui o valor presente dos lucros futuros."
    }},
    {{
      "name": "Inflação (CPI)",
      "status": "Elevada",
      "impact_on_ticker": "Negativo. Pode reduzir as margens da empresa se os custos aumentarem mais rápido que os preços."
    }}
  ]
}}
```

Agora, execute a análise para o ticker `{ticker}` com base na seguinte consulta do usuário: "{query}"
"""

# Definição do expert para ser descoberto pelo orquestrador
expert_definition = ExpertDefinition(
    name="macro",
    prompt_template=MACRO_ANALYSIS_PROMPT_TEMPLATE,
    response_model=MacroAnalysisSignal,
    model_name="phinance-instruct"  # Modelo especialista em finanças
)
