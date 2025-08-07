# -*- coding: utf-8 -*-
"""
Testes para o módulo de configuração (config.py).
"""

import pytest
from superezio_enterprise.config import EnterpriseConfig, CONFIG

def test_config_singleton_creation():
    """Testa se a instância global CONFIG é criada corretamente."""
    assert isinstance(CONFIG, EnterpriseConfig)
    assert CONFIG.max_concurrent_tasks > 0  # Garante que a validação básica passou

def test_enterprise_config_defaults():
    """Testa se os valores padrão da configuração são definidos como esperado."""
    config = EnterpriseConfig()
    assert config.max_concurrent_tasks == 50
    assert config.cache_ttl_seconds == 3600
    assert config.log_level == "INFO"
    assert config.streaming_enabled is True
    assert config.caching_enabled is True

def test_enterprise_config_post_init_validation():
    """Testa se a validação post-init levanta erros para valores inválidos."""
    with pytest.raises(ValueError, match="max_concurrent_tasks deve ser um valor positivo."):
        EnterpriseConfig(max_concurrent_tasks=0)

    with pytest.raises(ValueError, match="cache_ttl_seconds não pode ser negativo."):
        EnterpriseConfig(cache_ttl_seconds=-1)

    with pytest.raises(ValueError, match="max_memory_mb deve ser um valor positivo."):
        EnterpriseConfig(max_memory_mb=0)

    with pytest.raises(ValueError, match="rate_limit_per_minute deve ser um valor positivo."):
        EnterpriseConfig(rate_limit_per_minute=-100)

    with pytest.raises(ValueError, match="max_message_length deve ser um valor positivo."):
        EnterpriseConfig(max_message_length=0)

def test_config_allowed_file_types():
    """Testa se a lista de tipos de arquivo permitidos é criada corretamente."""
    config = EnterpriseConfig()
    assert isinstance(config.allowed_file_types, list)
    assert ".pdf" in config.allowed_file_types
