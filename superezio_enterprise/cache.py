# -*- coding: utf-8 -*-
"""
Módulo de Cache Inteligente

Fornece um sistema de cache em memória, thread-safe, com tempo de vida (TTL)
configurável e uma política de evicção LRU (Least Recently Used) para gerenciar
o tamanho do cache de forma eficiente.
"""

import time
import threading
import logging
from typing import Dict, Any, Optional

from .config import CONFIG

# Logger configurado para o módulo
logger = logging.getLogger(f"superezio_enterprise.{__name__}")


class IntelligentCache:
    """
    Gerenciador de cache em memória com política de evicção LRU e suporte a TTL.

    Este gerenciador é um singleton thread-safe. Ele armazena itens até um
    `max_size` configurado. Quando o cache está cheio, o item menos recentemente
    usado é removido para dar espaço a um novo. Itens também expiram após um TTL.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.max_size = CONFIG.cache_max_items
        self.default_ttl = CONFIG.cache_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = (
            threading.RLock()
        )  # RLock para permitir locks aninhados se necessário
        self._initialized = True

        if CONFIG.caching_enabled:
            logger.info(
                "IntelligentCache (Singleton) inicializado: maxSize=%d, defaultTTL=%d s",
                self.max_size,
                self.default_ttl,
            )
        else:
            logger.warning(
                "O sistema de cache está DESABILITADO globalmente via configuração."
            )

    def get(self, key: str) -> Optional[Any]:
        """
        Recupera um item do cache. Retorna None se não encontrado, expirado ou se o cache estiver desabilitado.
        Atualiza o tempo de acesso do item (marcando-o como recentemente usado).
        """
        if not CONFIG.caching_enabled:
            return None

        with self._lock:
            entry = self._cache.get(key)
            if not entry:
                logger.debug("Cache MISS para a chave: '%s'", key)
                return None

            if time.monotonic() > entry["expires_at"]:
                logger.info("Cache MISS (expirado) para a chave: '%s'. Removendo.", key)
                self._evict(key)
                return None

            self._access_times[key] = time.monotonic()
            logger.debug("Cache HIT para a chave: '%s'", key)
            return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Adiciona um item ao cache. Se o cache estiver cheio, remove o item menos usado.
        Não faz nada se o cache estiver desabilitado.
        """
        if not CONFIG.caching_enabled:
            return

        with self._lock:
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            ttl_to_use = ttl if ttl is not None else self.default_ttl
            self._cache[key] = {
                "value": value,
                "expires_at": time.monotonic() + ttl_to_use,
            }
            self._access_times[key] = time.monotonic()
            logger.info(
                "Cache SET para a chave: '%s' com TTL de %d segundos.", key, ttl_to_use
            )

    def _evict_lru(self) -> None:
        """Remove o item menos recentemente usado. Deve ser chamado dentro de um lock."""
        if not self._access_times:
            return

        lru_key = min(self._access_times, key=self._access_times.get)
        logger.info(
            "Cache cheio. Removendo item menos recentemente usado para liberar espaço: '%s'",
            lru_key,
        )
        self._evict(lru_key)

    def _evict(self, key: str) -> None:
        """Remove um item específico do cache e dos tempos de acesso. Deve ser chamado dentro de um lock."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_times:
            del self._access_times[key]

    def clear(self) -> None:
        """Limpa todo o conteúdo do cache."""
        with self._lock:
            self._cache.clear()
            self._access_times.clear()
            logger.warning("Todo o cache foi limpo manualmente.")


# --- Instância Global ---
# A instância singleton do IntelligentCache que será usada em toda a aplicação.
cache = IntelligentCache()
