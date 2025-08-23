# -*- coding: utf-8 -*-
"""
Expert: Analista de Risco.

Este módulo define a lógica e os prompts para o expert focado em
identificar e avaliar os riscos associados a um ativo.
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import List

from api.experts.base import ExpertDefinition

class RiskLevelEnum(str, Enum):
    """Enumeração dos possíveis níveis de risco."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class RiskFactor(BaseModel):
    """Schema para um fator de risco específico."""
    risk_type: str = Field(..., description="Tipo de risco (ex: 'Regulatório', 'Competitivo', 'Operacional', 'Mercado').")
    description: str = Field(..., description="Descrição do risco específico.")
    severity: RiskLevelEnum = Field(..., description="A severidade potencial do risco.")

class RiskAnalysisSignal(BaseModel):
    """
    Schema para a avaliação final de risco.
    """
    overall_risk_level: RiskLevelEnum = Field(..., description="O nível de risco agregado para o ativo.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nível de confiança na avaliação de risco.")
    summary: str = Field(..., description="Um resumo dos principais riscos que o ativo enfrenta.")
    key_risks: List[RiskFactor] = Field(..., description="Uma lista dos principais fatores de risco identificados.")

# Prompt para o Expert de Análise de Risco
RISK_ANALYSIS_PROMPT_TEMPLATE = """
Você é um Chief Risk Officer (CRO) de uma grande instituição financeira. Sua missão é identificar, analisar e quantificar os riscos associados a um investimento em um determinado ativo.

**REGRAS ESTRITAS:**
1.  **Formato de Saída:** Sua resposta DEVE ser um único objeto JSON.
2.  **Schema Obrigatório:** O JSON deve seguir EXATAMENTE o schema abaixo.
3.  **Análise Focada:** Identifique os riscos mais pertinentes para o ticker `{ticker}`. Pense em riscos de mercado, regulatórios, competitivos, tecnológicos e operacionais.
4.  **Não Emita Opinião de Investimento:** Sua análise deve focar exclusivamente no risco. Não forneça uma recomendação de compra ou venda.

**TAREFA:**
Realize uma análise de risco para o ticker **{ticker}**. Com base na sua análise, gere um objeto JSON.

**SCHEMA JSON DE SAÍDA OBRIGATÓRIO:**
```json
{{
  "overall_risk_level": "LOW" | "MEDIUM" | "HIGH",
  "confidence": float (0.0 a 1.0),
  "summary": "string",
  "key_risks": [
    {{
      "risk_type": "string",
      "description": "string",
      "severity": "LOW" | "MEDIUM" | "HIGH"
    }}
  ]
}}
```

**EXEMPLO DE SAÍDA JSON VÁLIDA:**
```json
{{
  "overall_risk_level": "MEDIUM",
  "confidence": 0.85,
  "summary": "O principal risco para {ticker} é a crescente pressão regulatória no setor de tecnologia, que pode impactar suas margens. Além disso, a concorrência está se intensificando, ameaçando sua participação de mercado.",
  "key_risks": [
    {{
      "risk_type": "Regulatório",
      "description": "Novas leis de antitruste e privacidade de dados sendo consideradas nos EUA e na Europa.",
      "severity": "HIGH"
    }},
    {{
      "risk_type": "Competitivo",
      "description": "Novos entrantes com tecnologias inovadoras estão ganhando tração no mercado principal da empresa.",
      "severity": "MEDIUM"
    }},
    {{
      "risk_type": "Mercado",
      "description": "A alta avaliação da empresa a torna vulnerável a uma correção de mercado ou mudança no sentimento do investidor.",
      "severity": "MEDIUM"
    }}
  ]
}}
```

Agora, execute a análise para o ticker `{ticker}` com base na seguinte consulta do usuário: "{query}"
"""

# Definição do expert para ser descoberto pelo orquestrador
expert_definition = ExpertDefinition(
    name="risk",
    prompt_template=RISK_ANALYSIS_PROMPT_TEMPLATE,
    response_model=RiskAnalysisSignal,
    model_name="phinance-instruct"  # Modelo especialista em finanças
)
