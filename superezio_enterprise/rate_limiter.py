# -*- coding: utf-8 -*-
"""
Módulo Rate Limiter (Limitador de Taxa)

Implementa um limitador de taxa global e thread-safe para proteger a aplicação
contra uso excessivo. Utiliza o algoritmo Token Bucket, que permite rajadas de
tráfego curtas e é ideal para controlar o acesso a APIs e recursos.
"""

import time
import threading
import logging

from .config import CONFIG

# Logger configurado para o módulo
logger = logging.getLogger(f"superezio_enterprise.{__name__}")


class RateLimiter:
    """
    Limitador de taxa thread-safe que usa o algoritmo Token Bucket.

    Este limitador é implementado como um singleton. Ele mantém um "balde" de tokens
    que é reabastecido a uma taxa constante. Cada requisição consome um ou mais
    tokens. Se não houver tokens suficientes, a requisição é bloqueada.
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

        self.rate = float(CONFIG.rate_limit_per_minute)
        self.per_seconds = 60.0
        self._tokens = self.rate
        self._last_update = time.monotonic()
        self._lock = threading.Lock()  # Lock da instância para proteger os tokens
        self._initialized = True

        self.tokens_per_second = self.rate / self.per_seconds
        logger.info(
            "Rate Limiter (Singleton) inicializado: Limite=%.2f reqs/min (%.2f tokens/s)",
            self.rate,
            self.tokens_per_second,
        )

    def acquire(self, tokens_to_consume: int = 1) -> bool:
        """
        Tenta adquirir um número de tokens para processar uma requisição.

        Args:
            tokens_to_consume: O número de tokens que a requisição custa. Padrão é 1.

        Returns:
            True se os tokens foram adquiridos com sucesso, False caso contrário.
        """
        with self._lock:
            now = time.monotonic()

            # Reabastece os tokens com base no tempo decorrido
            elapsed = now - self._last_update
            if elapsed > 0:
                new_tokens = elapsed * self.tokens_per_second
                self._tokens = min(self.rate, self._tokens + new_tokens)
                self._last_update = now

            # Verifica se há tokens suficientes
            if self._tokens >= tokens_to_consume:
                self._tokens -= tokens_to_consume
                logger.debug(
                    "Requisição permitida. Tokens consumidos: %d. Restantes: %.2f",
                    tokens_to_consume,
                    self._tokens,
                )
                return True
            else:
                logger.warning(
                    "Rate limit atingido. Requisição bloqueada. Tokens necessários: %d, disponíveis: %.2f",
                    tokens_to_consume,
                    self._tokens,
                )
                return False


# --- Instância Global ---
# A instância singleton do RateLimiter que será usada em toda a aplicação.
rate_limiter = RateLimiter()
