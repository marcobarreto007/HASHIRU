# -*- coding: utf-8 -*-
"""
Arquivo Principal (Main) - Ponto de Entrada e Demonstração Integrada

Orquestra a inicialização da aplicação Superezio Enterprise e executa um fluxo
de operações assíncrono e abrangente para demonstrar a integração de todos os
módulos, com foco no novo sistema de monitoramento e alocação de GPUs.
"""
import os
import sys

# garante que a pasta-pai (project root) esteja no Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import logging

# --- 1. Módulos de Configuração e Inicialização ---
from superezio_enterprise.config import CONFIG
from superezio_enterprise.logging_setup import setup_enterprise_logging
from superezio_enterprise.correlation import (
    CorrelationContext,
    correlation_id,
    session_id,
)

# --- 2. Módulos de Negócio e Utilitários (Singletons) ---
from superezio_enterprise.commands import command_dispatcher
from superezio_enterprise.session_manager import session_manager
from superezio_enterprise.hardware import hardware_manager

# --- Inicialização do Logging ---
logger = setup_enterprise_logging()


def initialize_app():
    """
    Prepara e inicializa todos os subsistemas da aplicação.
    """
    logger.info("--- Iniciando Superezio Enterprise com Monitoramento de GPU ---")
    logger.info("Módulos inicializados.")


async def run_gpu_demonstration_flow():
    """
    Executa um fluxo de operações para demonstrar o monitoramento e alocação de GPUs.
    """
    async with CorrelationContext(operation_name="GpuDemonstrationFlow") as ctx:
        # Atualiza o context vars
        correlation_id.set(ctx.corr_id)

        if not getattr(hardware_manager, "is_initialized", True):
            logger.error(
                "Hardware Manager não inicializado corretamente. Abortando demonstração."
            )
            return

        # 1. Criação da Sessão
        sid = session_manager.create_session(user_id="gpu_test_user")
        session_id.set(sid)

        # 2. Alocação de Modelos
        logger.info("--- Iniciando Alocação de Modelos ---")
        hardware_manager.assign_model_to_gpu(
            "large-language-model-v1", required_vram_mb=8000
        )
        hardware_manager.assign_model_to_gpu("text-embedder-v2", required_vram_mb=2000)
        hardware_manager.assign_model_to_gpu(
            "ultra-high-res-gan", required_vram_mb=15000
        )

        # 3. Monitoramento Contínuo
        logger.info("--- Iniciando Monitoramento ao Vivo por 15 segundos ---")
        for i in range(5):
            report = hardware_manager.get_live_report()
            print(f"\n--- Relatório de Status das GPUs (Ciclo {i+1}) ---")
            for gpu_id, state in report.items():
                print(f"GPU {gpu_id}: {state.name}")
                print(
                    f"  Temp: {state.temperature_c}°C | Utilização: {state.utilization_percent}%"
                )
                print(
                    f"  VRAM: {state.used_memory_mb:.2f}/{state.total_memory_mb:.2f} MB (Livre: {state.free_memory_mb:.2f} MB)"
                )
            await asyncio.sleep(CONFIG.gpu_monitoring_interval_seconds)

        # 4. Liberação de Modelos
        logger.info("--- Liberando Modelos ---")
        hardware_manager.release_model("large-language-model-v1")
        hardware_manager.release_model("text-embedder-v2")

        # 5. Health Check Final
        status = await command_dispatcher.dispatch_async("system:health_check")
        logger.info("Relatório de Saúde Final: %s", status)


async def main():
    """Ponto de entrada assíncrono principal que executa a aplicação."""
    try:
        initialize_app()
        await run_gpu_demonstration_flow()
    except Exception:
        logger.critical("Exceção não tratada no nível superior.", exc_info=True)
    finally:
        hardware_manager.shutdown()  # Fecha recursos NVML
        logger.info("--- Superezio Enterprise Finalizado ---")
        logging.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
