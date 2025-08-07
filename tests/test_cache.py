# -*- coding: utf-8 -*-
"""
Testes para o IntelligentCache (cache.py).
"""

import pytest
import time
from unittest.mock import patch

from superezio_enterprise.cache import IntelligentCache
from superezio_enterprise.config import EnterpriseConfig

@pytest.fixture
def mock_config():
    """Fornece uma configuração mockada para isolar os testes do cache."""
    return EnterpriseConfig(
        cache_max_items=3,      # Tamanho pequeno para facilitar testes de evicção
        cache_ttl_seconds=10,   # TTL curto para testes de expiração
        caching_enabled=True    # Garante que o cache esteja habilitado
    )

@pytest.fixture
def cache_instance(mock_config):
    """Fornece uma instância limpa do IntelligentCache para cada teste."""
    # Como IntelligentCache é um singleton, precisamos garantir um estado limpo
    # para cada teste, aplicando a configuração mockada.
    with patch('superezio_enterprise.cache.CONFIG', mock_config):
        instance = IntelligentCache()
        instance.max_size = mock_config.cache_max_items
        instance.default_ttl = mock_config.cache_ttl_seconds
        instance.clear()  # Garante que o cache está vazio no início do teste
        yield instance
        instance.clear() # Limpa após o teste

def test_cache_singleton(cache_instance):
    """Testa se o IntelligentCache segue o padrão singleton."""
    instance1 = cache_instance
    instance2 = IntelligentCache()
    assert instance1 is instance2

def test_set_and_get(cache_instance):
    """Testa a funcionalidade básica de adicionar e recuperar um item."""
    cache_instance.set("key1", "value1")
    assert cache_instance.get("key1") == "value1"

def test_get_nonexistent_key(cache_instance):
    """Testa a recuperação de uma chave que não existe."""
    assert cache_instance.get("nonexistent") is None

def test_cache_expiration(cache_instance):
    """Testa se um item do cache expira após o seu TTL."""
    cache_instance.set("key_exp", "value_exp", ttl=0.02)
    time.sleep(0.05)
    assert cache_instance.get("key_exp") is None

def test_lru_eviction(cache_instance):
    """Testa se a política de evicção LRU remove o item menos usado."""
    cache_instance.set("key1", "value1")
    time.sleep(0.01)
    cache_instance.set("key2", "value2")
    time.sleep(0.01)
    cache_instance.set("key3", "value3") # Cache está cheio (tamanho 3)

    # Acessa key1 para torná-lo o mais recentemente usado
    cache_instance.get("key1")
    time.sleep(0.01)

    # Adiciona um novo item, o que deve causar a evicção de key2 (o menos usado)
    cache_instance.set("key4", "value4")

    assert cache_instance.get("key1") == "value1"
    assert cache_instance.get("key2") is None  # Deve ter sido removido
    assert cache_instance.get("key3") is not None
    assert cache_instance.get("key4") is not None

def test_clear_cache(cache_instance):
    """Testa se o método clear remove todos os itens."""
    cache_instance.set("key1", "value1")
    cache_instance.set("key2", "value2")
    cache_instance.clear()
    assert cache_instance.get("key1") is None
    assert cache_instance.get("key2") is None
    assert len(cache_instance._cache) == 0
    assert len(cache_instance._access_times) == 0

def test_cache_disabled(mock_config):
    """Testa se as operações do cache são ignoradas quando ele está desabilitado."""
    mock_config.caching_enabled = False
    with patch('superezio_enterprise.cache.CONFIG', mock_config):
        cache_instance = IntelligentCache()
        cache_instance.clear()

        cache_instance.set("key1", "value1")
        assert cache_instance.get("key1") is None
        assert len(cache_instance._cache) == 0

        cache_instance.clear() # Apenas para garantir que não falha
