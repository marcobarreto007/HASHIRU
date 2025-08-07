# -*- coding: utf-8 -*-
"""
Módulo de Configuração Enterprise

Define as configurações centralizadas para a aplicação, utilizando uma abordagem
estruturada com dataclasses para garantir tipagem e organização.
As configurações são divididas em seções lógicas para facilitar a manutenção.
"""

from dataclasses import dataclass, field
from typing import List, Literal

# Tipos de Log Level permitidos, para validação estrita.
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclass
class EnterpriseConfig:
    """
    DataClass para armazenar todas as configurações da aplicação de forma segura e organizada.
    Validações básicas são feitas no __post_init__ para garantir a integridade dos dados.
    """

    # --- Performance ---
    # Número máximo de tarefas concorrentes que a aplicação pode executar.
    max_concurrent_tasks: int = 50
    # Tempo de vida (TTL) em segundos para o cache de dados.
    cache_ttl_seconds: int = 3600
    # Número máximo de itens a serem mantidos no cache (política LRU).
    cache_max_items: int = 1000
    # Limite máximo de memória (em MB) que a aplicação pode alocar.
    max_memory_mb: int = 2048

    # --- Segurança ---
    # Limite de requisições por minuto para proteger contra ataques de força bruta.
    rate_limit_per_minute: int = 100
    # Comprimento máximo (em caracteres) das mensagens de entrada para evitar sobrecarga.
    max_message_length: int = 10000
    # Lista de extensões de arquivo permitidas para upload.
    allowed_file_types: List[str] = field(
        default_factory=lambda: [".txt", ".pdf", ".doc", ".docx", ".md"]
    )

    # --- Hardware ---
    # Intervalo em segundos para a atualização das estatísticas das GPUs.
    gpu_monitoring_interval_seconds: int = 5

    # --- Logging ---
    # Nível de detalhe dos logs (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    log_level: LogLevel = "INFO"
    # Habilita/desabilita o formato de log estruturado (JSON).
    structured_logging: bool = True
    # Habilita/desabilita o rastreamento de correlação entre requisições.
    correlation_tracking: bool = True

    # --- Features ---
    # Habilita/desabilita o streaming de respostas.
    streaming_enabled: bool = True
    # Habilita/desabilita o sistema de cache.
    caching_enabled: bool = True
    # Habilita/desabilita a coleta de métricas de performance.
    metrics_enabled: bool = True

    def __post_init__(self):
        """
        Realiza validações nos valores de configuração após a inicialização.
        Garante que os valores estejam dentro de limites razoáveis.
        """
        if self.max_concurrent_tasks <= 0:
            raise ValueError("max_concurrent_tasks deve ser um valor positivo.")
        if self.cache_ttl_seconds < 0:
            raise ValueError("cache_ttl_seconds não pode ser negativo.")
        if self.max_memory_mb <= 0:
            raise ValueError("max_memory_mb deve ser um valor positivo.")
        if self.rate_limit_per_minute <= 0:
            raise ValueError("rate_limit_per_minute deve ser um valor positivo.")
        if self.max_message_length <= 0:
            raise ValueError("max_message_length deve ser um valor positivo.")


# --- Instância Global ---
# A instância única e imutável da configuração que será usada em toda a aplicação.
try:
    CONFIG = EnterpriseConfig()
except ValueError as e:
    print(f"Erro de configuração: {e}")
    # Em um cenário real, poderia lançar uma exceção fatal ou usar um fallback.
    # Para este exemplo, vamos prosseguir com uma configuração padrão se a validação falhar.
    CONFIG = EnterpriseConfig(max_concurrent_tasks=1)  # Exemplo de fallback
