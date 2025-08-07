# -*- coding: utf-8 -*-
"""
Módulo Health Manager (Gerenciador de Saúde)

Centraliza as verificações de saúde da aplicação. Permite registrar e executar
"health checks" para diferentes componentes (ex: banco de dados, serviços externos,
memória) e agrega os resultados em um relatório de estado unificado.
"""

import logging
import asyncio
from typing import Dict, Any, Callable, Tuple, Awaitable

from .circuit_breaker import AsyncCircuitBreaker, CircuitState
from .hardware import get_hardware_manager

# Logger configurado para o módulo
logger = logging.getLogger(f"superezio_enterprise.{__name__}")

# Tipo para uma função de verificação de saúde (pode ser síncrona ou assíncrona)
HealthCheckCallable = Callable[[], Awaitable[Tuple[bool, str]]]


class HealthManager:
    """
    Gerenciador de verificações de saúde que agrega o estado de vários componentes.
    Implementado como um singleton para ser acessível de toda a aplicação.
    Suporta verificações de saúde síncronas e assíncronas.
    """

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            # O lock aqui é mais para o asyncio, o __init__ ainda precisa de um lock de thread
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.checks: Dict[str, HealthCheckCallable] = {}
        self.circuit_breakers: Dict[str, AsyncCircuitBreaker] = {}
        self._initialized = True
        self._register_default_checks()
        logger.info("Health Manager (Singleton) inicializado.")

    def _register_default_checks(self):
        """Registra as verificações de saúde padrão do sistema."""

        # Health check para as GPUs
        async def gpu_health_check() -> Tuple[bool, str]:
            if not get_hardware_manager().is_initialized:
                return (
                    True,
                    "Nenhuma GPU NVIDIA encontrada ou NVML não pôde ser inicializada.",
                )

            gpu_report = get_hardware_manager().get_live_report()
            unhealthy_gpus = []
            for gpu_id, state in gpu_report.items():
                if state.temperature_c > 90:
                    unhealthy_gpus.append(
                        f"GPU {gpu_id} ({state.name}) está superaquecendo: {state.temperature_c}°C"
                    )

            if unhealthy_gpus:
                return False, " ; ".join(unhealthy_gpus)
            return True, "Todas as GPUs estão operando em temperaturas normais."

        self.register_check("gpu_status", gpu_health_check)

    def register_check(self, name: str, check_function: HealthCheckCallable):
        """
        Registra uma nova verificação de saúde assíncrona.
        """
        self.checks[name] = check_function
        logger.info(f"Verificação de saúde assíncrona '{name}' registrada.")

    def register_circuit_breaker(self, name: str, breaker: AsyncCircuitBreaker):
        """
        Registra um AsyncCircuitBreaker para que seu estado seja incluído no relatório de saúde.
        """
        self.circuit_breakers[name] = breaker
        logger.info(
            f"AsyncCircuitBreaker '{name}' registrado para monitoramento de saúde."
        )

    async def get_health_status(self) -> Dict[str, Any]:
        """
        Executa todas as verificações de saúde registradas (síncronas e assíncronas)
        e retorna um relatório de estado agregado.
        """
        logger.debug("Executando todas as verificações de saúde...")
        report: Dict[str, Any] = {"overall_status": "HEALTHY", "components": {}}
        all_healthy = True

        # Executa os health checks em paralelo
        check_tasks = [
            self._run_check(name, func) for name, func in self.checks.items()
        ]
        results = await asyncio.gather(*check_tasks)

        for name, result in results:
            report["components"][name] = result
            if result["status"] == "UNHEALTHY":
                all_healthy = False

        # Verifica os circuit breakers (síncrono)
        for name, breaker in self.circuit_breakers.items():
            state = breaker.state
            is_healthy = state != CircuitState.OPEN
            status = "HEALTHY" if is_healthy else "UNHEALTHY"
            report["components"][name] = {
                "status": status,
                "circuit_state": state.value,
            }
            if not is_healthy:
                all_healthy = False

        if not all_healthy:
            report["overall_status"] = "UNHEALTHY"
            logger.warning(
                "Relatório de saúde final: %s. Detalhes: %s",
                report["overall_status"],
                report["components"],
            )
        else:
            logger.info("Relatório de saúde final: %s", report["overall_status"])

        return report

    async def _run_check(
        self, name: str, func: HealthCheckCallable
    ) -> Tuple[str, Dict[str, Any]]:
        """Wrapper para executar uma única verificação de saúde e tratar exceções."""
        try:
            is_healthy, message = await func()
            status = "HEALTHY" if is_healthy else "UNHEALTHY"
            return name, {"status": status, "message": message}
        except Exception as e:
            logger.error(
                "Exceção ao executar a verificação de saúde '%s'.", name, exc_info=True
            )
            return name, {"status": "UNHEALTHY", "error": str(e)}


# Instância singleton do gerenciador de saúde
health_manager = HealthManager()
