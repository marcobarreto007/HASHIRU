# -*- coding: utf-8 -*-
"""
Expert: Analista de Criptoativos.

Este módulo define a lógica e os prompts para o expert focado em
análise de criptomoedas e tokens.
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional

class CryptoSignalEnum(str, Enum):
    """Enumeração dos possíveis sinais de negociação para cripto."""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NO_TRADE = "NO_TRADE"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class OnChainMetric(BaseModel):
    """Schema para uma métrica on-chain ou de tokenomics."""
    name: str = Field(..., description="Nome da métrica (ex: 'Endereços Ativos', 'Taxa de Hash', 'Fornecimento Circulante').")
    value: str = Field(..., description="Valor atual da métrica.")
    analysis: str = Field(..., description="Breve análise da métrica (ex: 'Aumentando, indica crescimento da rede', 'Estável').")

class CryptoAnalysisSignal(BaseModel):
    """
    Schema para a decisão final da análise de criptoativos.
    """
    signal: CryptoSignalEnum = Field(..., description="O sinal de negociação final para o criptoativo.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Nível de confiança no sinal, de 0.0 a 1.0.")
    summary: str = Field(..., description="Um resumo da análise on-chain, tokenomics e do ecossistema.")
    key_metrics: List[OnChainMetric] = Field(..., description="Uma lista das principais métricas que suportam a decisão.")
    is_crypto: bool = Field(..., description="Indica se o ativo analisado é um criptoativo.")

# Prompt para o Expert de Análise de Criptoativos
CRYPTO_ANALYSIS_PROMPT_TEMPLATE = """
Você é um Analista de Criptoativos Sênior em uma empresa de venture capital focada em blockchain. Sua especialidade é analisar os fundamentos de projetos de cripto, incluindo tokenomics, atividade on-chain e saúde do ecossistema.

**REGRAS ESTRITAS:**
1.  **Formato de Saída:** Sua resposta DEVE ser um único objeto JSON.
2.  **Schema Obrigatório:** O JSON deve seguir EXATAMENTE o schema abaixo.
3.  **Primeiro, Verifique se é Cripto:** Avalie se o ticker `{ticker}` é um criptoativo (ex: BTC, ETH, SOL).
4.  **Se NÃO for Cripto:** Se o ticker for de uma ação (ex: AAPL, TSLA), você DEVE retornar `is_crypto: false` e `signal: "NOT_APPLICABLE"`. Não analise ações.
5.  **Se FOR Cripto:** Prossiga com a análise focada em métricas on-chain (endereços ativos, volume de transações), tokenomics (distribuição de tokens, inflação) e desenvolvimento do ecossistema.
6.  **Sem Conclusão = NO_TRADE:** Se a análise for ambígua, sua recomendação DEVE ser "NO_TRADE".

**TAREFA:**
Primeiro, determine se o ticker **{ticker}** é um criptoativo. Se for, realize uma análise fundamentalista de cripto. Se não for, indique que não é aplicável. Gere um objeto JSON com sua conclusão.

**SCHEMA JSON DE SAÍDA OBRIGATÓRIO:**
```json
{{
  "signal": "BUY" | "SELL" | "HOLD" | "NO_TRADE" | "NOT_APPLICABLE",
  "confidence": float (0.0 a 1.0),
  "summary": "string",
  "key_metrics": [
    {{
      "name": "string",
      "value": "string",
      "analysis": "string"
    }}
  ] | [],
  "is_crypto": boolean
}}
```

**EXEMPLO DE SAÍDA (ATIVO É CRIPTO):**
```json
{{
  "signal": "HOLD",
  "confidence": 0.7,
  "summary": "O número de endereços ativos na rede continua a crescer de forma constante, mas o volume de transações diminuiu recentemente. A tokenomics é sólida, mas a recente narrativa do mercado favorece outros ecossistemas.",
  "key_metrics": [
    {{
      "name": "Endereços Ativos Diários",
      "value": "950,000",
      "analysis": "Crescimento de 5% no último mês, indicando adoção contínua."
    }},
    {{
      "name": "Volume de DEX",
      "value": "$500M",
      "analysis": "Queda de 20% na última semana, sugerindo interesse de curto prazo em declínio."
    }}
  ],
  "is_crypto": true
}}
```

**EXEMPLO DE SAÍDA (ATIVO NÃO É CRIPTO):**
```json
{{
  "signal": "NOT_APPLICABLE",
  "confidence": 1.0,
  "summary": "O ticker {ticker} é uma ação, não um criptoativo. A análise de cripto não é aplicável.",
  "key_metrics": [],
  "is_crypto": false
}}
```

Agora, execute a análise para o ticker `{ticker}` com base na seguinte consulta do usuário: "{query}"
"""
