# -*- coding: utf-8 -*-
"""
Expert: Analista Técnico Quantitativo.

Este módulo define a lógica e os prompts para o expert focado em
análise técnica de ativos financeiros.
"""

from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import List, Optional

class SignalEnum(str, Enum):
    """Enumeração dos possíveis sinais de negociação."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NO_TRADE = "NO_TRADE"

class TechnicalIndicator(BaseModel):
    """Schema para um indicador técnico específico."""
    name: str = Field(..., description="Nome do indicador (ex: 'RSI (14)', 'MACD (12,26,9)').")
    value: str = Field(..., description="Valor atual do indicador.")
    interpretation: str = Field(..., description="Interpretação do indicador (ex: 'Sobrecomprado', 'Cruzamento de alta').")

class TechnicalAnalysisSignal(BaseModel):
    """
    Schema para a decisão final da análise técnica.
    Este é o formato JSON que o LLM deve retornar.
    """
    signal: SignalEnum = Field(..., description="O sinal de negociação final.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nível de confiança no sinal, de 0.0 a 1.0.")
    summary: str = Field(..., description="Um resumo conciso da análise e da lógica por trás da decisão.")
    key_indicators: List[TechnicalIndicator] = Field(..., description="Uma lista dos principais indicadores técnicos que suportam a decisão.")
    price_target: Optional[float] = Field(None, description="Preço-alvo estimado, se aplicável.")
    stop_loss: Optional[float] = Field(None, description="Preço de stop-loss sugerido, se aplicável.")

    @field_validator('signal', mode='before')
    def upper_case_signal(cls, v):
        return v.upper()

from api.experts.base import ExpertDefinition

# Prompt para o Expert de Análise Técnica
# Este prompt foi cuidadosamente desenhado para forçar o LLM a retornar um JSON estruturado.
TECHNICAL_ANALYSIS_PROMPT_TEMPLATE = """
Você é um Analista Técnico Quantitativo Sênior para um fundo de hedge de elite. Sua única tarefa é fornecer uma análise técnica concisa e acionável para o próximo dia de negociação (overnight).

**REGRAS ESTRITAS:**
1.  **Formato de Saída:** Sua resposta DEVE ser um único objeto JSON, sem nenhum outro texto ou explicação antes ou depois.
2.  **Schema Obrigatório:** O JSON deve seguir EXATAMENTE o schema abaixo. Não adicione, remova ou modifique nenhum campo.
3.  **Análise Focada:** Analise o ativo `{ticker}` com base em um gráfico diário. Use apenas os indicadores técnicos mais comuns (RSI, MACD, Médias Móveis, Bandas de Bollinger).
4.  **Sem Conclusão = NO_TRADE:** Se a análise for ambígua ou os indicadores forem conflitantes, sua recomendação DEVE ser "NO_TRADE". Não force uma recomendação.
5.  **Confiança é Chave:** O nível de confiança deve refletir realisticamente a força da convergência dos indicadores. Uma confiança alta (>0.8) exige um alinhamento claro de múltiplos indicadores.
6.  **Rationale é Essencial:** O resumo deve explicar o "porquê" da sua decisão de forma clara e direta.

**TAREFA:**
Realize uma análise técnica overnight para o ticker **{ticker}**. Com base na sua análise, gere um objeto JSON com sua recomendação.

**EXEMPLO DE PERGUNTA DO USUÁRIO:**
"analise tecnica overnight - AAPL diário"

**SCHEMA JSON DE SAÍDA OBRIGATÓRIO:**
```json
{{
  "signal": "BUY" | "SELL" | "HOLD" | "NO_TRADE",
  "confidence": float (0.0 a 1.0),
  "summary": "string",
  "key_indicators": [
    {{
      "name": "string",
      "value": "string",
      "interpretation": "string"
    }}
  ],
  "price_target": float | null,
  "stop_loss": float | null
}}
```

**EXEMPLO DE SAÍDA JSON VÁLIDA:**
```json
{{
  "signal": "BUY",
  "confidence": 0.75,
  "summary": "O ativo rompeu a média móvel de 50 dias com volume crescente, e o RSI (14) cruzou para cima de 50, indicando momentum de alta. O MACD está prestes a fazer um cruzamento de alta.",
  "key_indicators": [
    {{
      "name": "RSI (14)",
      "value": "55.2",
      "interpretation": "Momentum de alta, saiu da zona neutra."
    }},
    {{
      "name": "MME (50)",
      "value": "145.80",
      "interpretation": "Preço atual (146.50) cruzou acima da MME de 50 dias, um sinal de alta."
    }},
    {{
      "name": "MACD (12,26,9)",
      "value": "-0.5",
      "interpretation": "Linha do MACD prestes a cruzar a linha de sinal, indicando possível reversão de tendência."
    }}
  ],
  "price_target": 155.0,
  "stop_loss": 142.5
}}
```

Agora, execute a análise para o ticker `{ticker}` com base na seguinte consulta do usuário: "{query}"
"""

# Definição do expert para ser descoberto pelo orquestrador
expert_definition = ExpertDefinition(
    name="technical",
    prompt_template=TECHNICAL_ANALYSIS_PROMPT_TEMPLATE,
    response_model=TechnicalAnalysisSignal,
    model_name="phinance-instruct"  # Modelo especialista em finanças
)
