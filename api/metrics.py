# -*- coding: utf-8 -*-
"""
Módulo de Métricas Prometheus.

Este arquivo define as métricas customizadas que a aplicação expõe para
monitoramento e observabilidade.
"""

from prometheus_client import Counter, Gauge

# Métricas de Cache
# Usamos um Gauge para o status do backend para poder representar o estado atual (1 para ativo, 0 para inativo)
# No entanto, para o nome do backend, uma métrica de info é mais apropriada.
# Por simplicidade aqui, vamos focar nos contadores de HIT/MISS.

CACHE_HITS = Counter(
    "ezio_cache_hits_total",
    "Número total de acertos no cache.",
    ["backend"]  # Label para diferenciar entre 'redis' e 'memory'
)

CACHE_MISSES = Counter(
    "ezio_cache_misses_total",
    "Número total de falhas no cache (misses).",
    ["backend"]
)

# Métricas de Análise do Comitê
EXPERT_SUCCESS = Counter(
    "ezio_expert_success_total",
    "Número total de análises de expert bem-sucedidas.",
    ["expert_name"]
)

EXPERT_FAILURE = Counter(
    "ezio_expert_failure_total",
    "Número total de falhas na análise de expert.",
    ["expert_name"]
)

# Adicionar mais métricas conforme necessário...
