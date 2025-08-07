# -*- coding: utf-8 -*-
"""
Testes para o RateLimiter (rate_limiter.py).
"""

import pytest
import time
from unittest.mock import patch

from superezio_enterprise.rate_limiter import RateLimiter
from superezio_enterprise.config import EnterpriseConfig

@pytest.fixture
def mock_config():
    """Fornece uma configuração mockada para isolar os testes do limitador."""
    # Um limite baixo para facilitar o teste de esgotamento de tokens
    return EnterpriseConfig(rate_limit_per_minute=5)

@pytest.fixture
def limiter_instance(mock_config):
    """Fornece uma instância limpa do RateLimiter para cada teste."""
    # Como RateLimiter é um singleton, precisamos garantir um estado limpo
    with patch('superezio_enterprise.rate_limiter.CONFIG', mock_config):
        instance = RateLimiter()
        # Reinicializa o estado interno para o teste
        instance.rate = float(mock_config.rate_limit_per_minute)
        instance.per_seconds = 60.0
        instance._tokens = instance.rate
        instance._last_update = time.monotonic()
        instance.tokens_per_second = instance.rate / instance.per_seconds
        yield instance

def test_rate_limiter_singleton(limiter_instance):
    """Testa se o RateLimiter segue o padrão singleton."""
    instance1 = limiter_instance
    instance2 = RateLimiter()
    assert instance1 is instance2

def test_initial_tokens(limiter_instance):
    """Testa se o número inicial de tokens está correto."""
    assert limiter_instance._tokens == limiter_instance.rate

def test_acquire_success(limiter_instance):
    """Testa se é possível adquirir tokens quando há suficientes."""
    assert limiter_instance.acquire(1) is True
    assert limiter_instance.acquire(2) is True
    # 5 (inicial) - 1 - 2 = 2 tokens restantes
    assert limiter_instance._tokens == pytest.approx(2)

def test_acquire_failure_due_to_exhaustion(limiter_instance):
    """Testa se a aquisição falha quando não há tokens suficientes."""
    # Consome todos os 5 tokens iniciais
    assert limiter_instance.acquire(5) is True
    assert limiter_instance._tokens == pytest.approx(0)

    # A próxima tentativa deve falhar
    assert limiter_instance.acquire(1) is False

def test_token_refill(limiter_instance):
    """Testa se os tokens são reabastecidos ao longo do tempo."""
    # Esgota os tokens
    assert limiter_instance.acquire(5) is True
    assert limiter_instance.acquire(1) is False

    # O reabastecimento é de 5 tokens por 60 segundos, ou 1/12 tokens por segundo.
    # Esperar 12 segundos deve gerar 1 token.
    time.sleep(12)

    # A aquisição agora deve ser bem-sucedida
    assert limiter_instance.acquire(1) is True
    assert limiter_instance._tokens == pytest.approx(0, abs=0.1) # Pode haver uma pequena sobra

def test_acquire_burst(limiter_instance):
    """Testa se o balde de tokens permite rajadas (bursts)."""
    # O limite é 5, então uma rajada de 5 deve ser permitida
    assert limiter_instance.acquire(5) is True
    assert limiter_instance._tokens == pytest.approx(0)

def test_refill_does_not_exceed_capacity(limiter_instance):
    """Testa se o reabastecimento não ultrapassa a capacidade máxima."""
    # Consome 2 tokens
    limiter_instance.acquire(2)
    assert limiter_instance._tokens == pytest.approx(3)

    # Espera um tempo longo, que teoricamente geraria mais de 2 tokens
    time.sleep(36) # Deve gerar 3 tokens (5/60 * 36 = 3)

    # O número de tokens não deve exceder a capacidade máxima (5)
    limiter_instance.acquire(0) # Força a atualização do reabastecimento
    assert limiter_instance._tokens <= limiter_instance.rate
    assert limiter_instance._tokens == pytest.approx(5)
