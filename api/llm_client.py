# -*- coding: utf-8 -*-
"""
Ollama LLM Client.

Este módulo fornece um cliente para interagir com a API do Ollama,
permitindo a geração de texto a partir dos modelos de linguagem.
"""

import httpx
import json
import logging
import os
import asyncio
from typing import Dict, Any, Optional

# Configurar um logger para este módulo
logger = logging.getLogger(__name__)

class OllamaError(Exception):
    """Exceção base para erros relacionados ao cliente Ollama."""
    pass

class OllamaClient:
    """
    Um cliente assíncrono para interagir com a API do Ollama.
    """
    def __init__(self, host: str = "http://localhost:11434"):
        """
        Inicializa o cliente Ollama.

        Args:
            host (str): O host e a porta da API do Ollama.
        """
        self.host = host
        self.client = httpx.AsyncClient()
        logger.info(f"Cliente Ollama inicializado para o host: {self.host}")

    async def generate_ollama(
        self,
        model: str,
        prompt: str,
        timeout: int = 60,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Gera uma resposta de um modelo Ollama, esperando uma saída JSON.
        Pode retornar uma resposta mockada se a variável de ambiente EZIO_MOCK_LLM=true.

        Args:
            model (str): O nome do modelo a ser usado (ex: 'llama3').
            prompt (str): O prompt a ser enviado para o modelo.
            timeout (int): O tempo máximo de espera pela resposta em segundos.
            options (Optional[Dict[str, Any]]): Opções adicionais do Ollama.

        Returns:
            Dict[str, Any]: O objeto JSON retornado pelo modelo.

        Raises:
            OllamaError: Se ocorrer um erro na comunicação com a API ou no processamento.
        """
        # --- MODO MOCK ---
        if os.environ.get("EZIO_MOCK_LLM", "false").lower() == "true":
            logger.warning(f">>> MODO MOCK ATIVADO: Gerando resposta mockada para o modelo '{model}'. <<<")
            await asyncio.sleep(0.5) # Simular latência da rede
            return self._get_mock_response(prompt)

        # --- MODO REAL ---
        api_url = f"{self.host}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": options or {}
        }

        logger.debug(f"Enviando requisição para Ollama: {api_url}")

        try:
            response = await self.client.post(api_url, json=payload, timeout=timeout)
            response.raise_for_status()

            response_data = response.json()

            # O Ollama retorna o JSON como uma string no campo "response"
            if "response" in response_data and isinstance(response_data["response"], str):
                try:
                    json_content = json.loads(response_data["response"])
                    logger.info(f"Resposta JSON do modelo '{model}' recebida e parseada com sucesso.")
                    return json_content
                except json.JSONDecodeError as e:
                    logger.error(f"Erro ao decodificar o JSON da resposta do Ollama: {e}\nResposta recebida: {response_data['response']}")
                    raise OllamaError(f"Falha ao decodificar a resposta JSON do modelo: {e}")
            else:
                # Se o JSON já estiver parseado, retorne diretamente.
                # Isso pode acontecer dependendo da versão do Ollama ou se 'format' não for respeitado.
                if isinstance(response_data, dict) and "signal" in response_data:
                     logger.warning("A resposta do Ollama já era um JSON parseado, não uma string.")
                     return response_data
                logger.error(f"Resposta inesperada do Ollama: {response_data}")
                raise OllamaError("A resposta do Ollama não continha um campo 'response' em formato de string JSON.")

        except httpx.TimeoutException as e:
            logger.error(f"Timeout ao chamar a API do Ollama após {timeout}s: {e}")
            raise OllamaError(f"A requisição para o Ollama excedeu o tempo limite de {timeout} segundos.")
        except httpx.RequestError as e:
            logger.error(f"Erro de requisição ao chamar a API do Ollama: {e}")
            raise OllamaError(f"Não foi possível conectar ao Ollama em {self.host}. Verifique se o serviço está rodando.")
        except Exception as e:
            logger.exception("Erro inesperado ao interagir com o Ollama.")
            raise OllamaError(f"Ocorreu um erro inesperado: {e}")

    def _get_mock_response(self, prompt: str) -> Dict[str, Any]:
        """
        Retorna uma resposta JSON mockada com base no conteúdo do prompt.
        """
        # Analista Técnico
        if "Analista Técnico Quantitativo Sênior" in prompt:
            return {
                "signal": "BUY", "confidence": 0.75, "summary": "Mock Técnico: Ativo com forte momentum de alta.",
                "key_indicators": [{"name": "RSI (14)", "value": "65", "interpretation": "Próximo de sobrecompra"}],
                "price_target": 160.0, "stop_loss": 140.0
            }
        # Analista Fundamentalista
        if "Analista de Equity Research Sênior" in prompt:
            return {
                "signal": "BUY", "confidence": 0.8, "summary": "Mock Fundamental: Empresa com fundamentos sólidos e subvalorizada.",
                "key_metrics": [{"name": "P/L", "value": "15x", "analysis": "Abaixo da média do setor"}],
                "valuation": "Subvalorizado"
            }
        # Analista Macro
        if "Estrategista Macroeconômico Global" in prompt:
            return {
                "overall_impact": "NEUTRAL", "confidence": 0.6, "summary": "Mock Macro: Cenário macroeconômico misto, sem impacto claro.",
                "key_factors": [{"name": "Taxa de Juros", "status": "Estável", "impact_on_ticker": "Neutro"}]
            }
        # Analista de Risco
        if "Chief Risk Officer" in prompt:
            return {
                "overall_risk_level": "MEDIUM", "confidence": 0.85, "summary": "Mock Risco: Riscos regulatórios e de mercado são uma preocupação.",
                "key_risks": [{"risk_type": "Regulatório", "description": "Incerteza regulatória no setor.", "severity": "MEDIUM"}]
            }
        # Analista de Sentimento
        if "Analista de Dados Quantitativo" in prompt:
            return {
                "overall_sentiment": "BULLISH", "confidence": 0.7, "summary": "Mock Sentimento: Sentimento positivo nas notícias e entre analistas.",
                "key_sources": [{"source_type": "Notícias", "summary": "Cobertura positiva da mídia.", "sentiment": "BULLISH"}]
            }
        # Analista de Cripto
        if "Analista de Criptoativos Sênior" in prompt:
            # Simula o caso de uma ação, não cripto
            if "AAPL" in prompt:
                return {
                    "signal": "NOT_APPLICABLE", "confidence": 1.0, "summary": "Mock Cripto: O ticker não é um criptoativo.",
                    "key_metrics": [], "is_crypto": False
                }
            # Simula o caso de ser cripto
            return {
                "signal": "HOLD", "confidence": 0.6, "summary": "Mock Cripto: Atividade on-chain estável, mas sem grandes catalisadores.",
                "key_metrics": [{"name": "Endereços Ativos", "value": "1M", "analysis": "Estável"}],
                "is_crypto": True
            }

        # Fallback caso nenhum prompt corresponda
        logger.error(f"Nenhuma resposta mockada encontrada para o prompt: {prompt[:200]}...")
        return {"error": "No mock response found for this prompt."}

    async def close(self):
        """Fecha o cliente httpx."""
        await self.client.aclose()
        logger.info("Cliente Ollama fechado.")

    async def check_health(self) -> (bool, str):
        """
        Verifica a conectividade com a API do Ollama.
        Retorna uma tupla (is_healthy, status_message).
        """
        # Se estivermos em modo mock, consideramos o Ollama sempre saudável.
        if os.environ.get("EZIO_MOCK_LLM", "false").lower() == "true":
            return True, "OK (Mocked)"

        try:
            # A API do Ollama não tem um endpoint de health-check oficial como /health.
            # Uma maneira comum de verificar é fazer uma requisição leve, como listar modelos.
            # No entanto, uma simples requisição HEAD para a raiz deve ser suficiente e mais leve.
            response = await self.client.head(self.host, timeout=5)
            response.raise_for_status()
            return True, "OK"
        except httpx.RequestError as e:
            logger.warning(f"Falha na verificação de saúde do Ollama: {e}")
            return False, f"Connection Error: {e}"
        except httpx.HTTPStatusError as e:
            logger.warning(f"Falha na verificação de saúde do Ollama. Status: {e.response.status_code}")
            return False, f"HTTP Status Error: {e.response.status_code}"
        except Exception as e:
            logger.error(f"Erro inesperado na verificação de saúde do Ollama: {e}")
            return False, f"Unexpected Error: {e}"
