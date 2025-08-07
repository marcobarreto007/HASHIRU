# -*- coding: utf-8 -*-
"""
Módulo Async Circuit Breaker

Implementa uma versão assíncrona do padrão Circuit Breaker, projetada para
proteger a aplicação de falhas repetidas em serviços externos em um ambiente
asyncio. Ele monitora falhas, abre o circuito para interromper chamadas e tenta
se recuperar de forma não-bloqueante.
"""

import time
import asyncio
import logging
from enum import Enum
from typing import Callable, Any, Coroutine

# Logger configurado para o módulo
logger = logging.getLogger(f"superezio_enterprise.{__name__}")


class CircuitState(Enum):
    """Enumeração dos possíveis estados de um Circuit Breaker."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class AsyncCircuitBreaker:
    """
    Implementação de um Circuit Breaker assíncrono e thread-safe.

    Este disjuntor envolve chamadas de função (síncronas ou assíncronas) e as
    monitora. Se o número de falhas exceder o `failure_threshold`, o circuito
    abre. As chamadas subsequentes falham imediatamente por um período de
    `recovery_timeout` segundos. Após o timeout, o estado muda para HALF_OPEN,
    permitindo uma chamada de teste para verificar a recuperação do serviço.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._state = CircuitState.CLOSED
        self._lock = asyncio.Lock()  # Usa um Lock assíncrono

        logger.info(
            "AsyncCircuitBreaker instanciado: threshold=%d, timeout=%d s",
            self.failure_threshold,
            self.recovery_timeout,
        )

    @property
    def state(self) -> CircuitState:
        """Retorna o estado atual do disjuntor."""
        return self._state

    async def call(
        self, func: Callable[..., Coroutine], *args: Any, **kwargs: Any
    ) -> Any:
        """
        Executa a chamada assíncrona protegida pelo Circuit Breaker.

        Args:
            func: A função (coroutine) a ser executada.
            *args, **kwargs: Argumentos para a função.

        Returns:
            O resultado da função, se bem-sucedida.

        Raises:
            ConnectionError: Se o circuito estiver aberto.
            Exception: A exceção original da função em caso de falha.
        """
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                    self._change_state(CircuitState.HALF_OPEN)
                else:
                    logger.warning(
                        "Chamada para %s bloqueada. Circuito está ABERTO.",
                        func.__name__,
                    )
                    raise ConnectionError("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            logger.error(
                "Falha na chamada de %s. Registrando falha no Circuit Breaker.",
                func.__name__,
                exc_info=True,
            )
            await self._on_failure()
            raise e

    async def _on_success(self) -> None:
        """Reseta o disjuntor para o estado CLOSED após um sucesso."""
        async with self._lock:
            if self._state != CircuitState.CLOSED:
                self._change_state(CircuitState.CLOSED)
            self._failure_count = 0

    async def _on_failure(self) -> None:
        """Registra uma falha e abre o circuito se o limite for atingido."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if (
                self._state == CircuitState.HALF_OPEN
                or self._failure_count >= self.failure_threshold
            ):
                if self._state != CircuitState.OPEN:
                    self._change_state(CircuitState.OPEN)

    def _change_state(self, new_state: CircuitState) -> None:
        """Muda o estado do disjuntor e loga a transição. Deve ser chamado dentro de um lock."""
        if self._state != new_state:
            logger.warning(
                "Circuit Breaker mudou de estado: %s -> %s",
                self._state.value,
                new_state.value,
            )
            self._state = new_state


# --- Instâncias Globais ---
# Instâncias específicas para diferentes partes do sistema com diferentes sensibilidades.

# Breaker para automações internas: mais sensível, com timeout de recuperação curto.
automation_circuit_breaker = AsyncCircuitBreaker(
    failure_threshold=3, recovery_timeout=30
)

# Breaker para modelos de IA: mais tolerante a falhas, com timeout mais longo.
ai_model_circuit_breaker = AsyncCircuitBreaker(failure_threshold=5, recovery_timeout=60)
