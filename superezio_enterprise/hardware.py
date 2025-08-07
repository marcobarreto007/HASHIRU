# -*- coding: utf-8 -*-
"""
Módulo de Gerenciamento de Hardware (GPU NVIDIA)

Fornece uma interface para descobrir, monitorar e alocar modelos de IA em GPUs NVIDIA
conectadas ao sistema. Utiliza a biblioteca pynvml para interagir diretamente com
o driver da NVIDIA e obter dados em tempo real.
"""

import logging                              # Logging estruturado
import threading                            # Threads para monitoramento contínuo
import time                                 # Sleep nos loops de monitoramento
import dataclasses                          # Dataclass para GpuState
from typing import Dict, Any, Optional, List

from pynvml import (                        # Importações explícitas do pynvml
    nvmlInit,
    nvmlDeviceGetCount,
    nvmlDeviceGetHandleByIndex,
    nvmlDeviceGetMemoryInfo,
    nvmlDeviceGetUtilizationRates,
    nvmlDeviceGetTemperature,
    nvmlDeviceGetPowerUsage,
    nvmlDeviceGetName,
    nvmlShutdown,
    NVMLError,
    NVML_TEMPERATURE_GPU,
)

from .config import CONFIG                  # Configurações da aplicação

# Logger configurado para este módulo
logger = logging.getLogger("superezio_enterprise.hardware")


@dataclasses.dataclass
class GpuState:
    """
    Estado de uma GPU NVIDIA individual.
    """
    id: int
    name: str
    total_memory_mb: float
    free_memory_mb: float
    used_memory_mb: float
    utilization_percent: int
    temperature_c: int
    power_usage_w: float


class HardwareManager:
    """
    Singleton que gerencia descoberta, monitoramento e alocação de modelos em GPUs NVIDIA.
    """
    _instance: Optional["HardwareManager"] = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        # Implementa o padrão singleton
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Evita reinicialização múltipla
        if getattr(self, "_initialized", False):
            return

        self.is_initialized: bool = False
        self.gpu_count: int = 0
        self.gpu_handles: List[Any] = []
        self.gpu_states: Dict[int, GpuState] = {}
        self.assignments: Dict[str, int] = {}
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

        try:
            # Inicializa NVML e descobre GPUs
            nvmlInit()
            self.gpu_count = nvmlDeviceGetCount()
            if self.gpu_count == 0:
                logger.warning("Nenhuma GPU NVIDIA encontrada no sistema.")
            else:
                for i in range(self.gpu_count):
                    handle = nvmlDeviceGetHandleByIndex(i)
                    self.gpu_handles.append(handle)

                self.is_initialized = True
                self._initialized = True
                logger.info(f"NVML inicializada com sucesso. {self.gpu_count} GPUs encontradas.")

                # Primeira coleta síncrona de estados e inicia background
                self.update_all_gpu_states()
                self.start_monitoring()

        except NVMLError as e:
            logger.critical(f"Falha ao inicializar NVML: {e}")

    def start_monitoring(self):
        """Inicia thread daemon para monitoramento periódico."""
        if not self.is_initialized or self._monitor_thread:
            return
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"Monitoramento de GPU iniciado (intervalo: {CONFIG.gpu_monitoring_interval_seconds}s)")

    def _monitor_loop(self):
        """Loop que atualiza os estados enquanto não for sinalizado para parar."""
        while not self._stop_event.is_set():
            self.update_all_gpu_states()
            time.sleep(CONFIG.gpu_monitoring_interval_seconds)

    def update_all_gpu_states(self):
        """Coleta dados de todas as GPUs e popula self.gpu_states."""
        with self._lock:
            for idx, handle in enumerate(self.gpu_handles):
                mem = nvmlDeviceGetMemoryInfo(handle)
                util = nvmlDeviceGetUtilizationRates(handle)
                temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
                power = nvmlDeviceGetPowerUsage(handle) / 1000.0

                # Trata nome como bytes ou str
                raw_name = nvmlDeviceGetName(handle)
                if isinstance(raw_name, (bytes, bytearray)):
                    name = raw_name.decode("utf-8", errors="ignore")
                else:
                    name = raw_name

                self.gpu_states[idx] = GpuState(
                    id=idx,
                    name=name,
                    total_memory_mb=mem.total / (1024**2),
                    free_memory_mb=mem.free / (1024**2),
                    used_memory_mb=mem.used / (1024**2),
                    utilization_percent=util.gpu,
                    temperature_c=temp,
                    power_usage_w=power,
                )
        logger.debug("Estados das GPUs atualizados.")

    def assign_model_to_gpu(self, model_name: str, required_vram_mb: int) -> Optional[int]:
        """
        Atribui o modelo à GPU com VRAM livre suficiente e menor uso.
        Retorna o ID da GPU ou None se não houver capacidade.
        """
        with self._lock:
            if model_name in self.assignments:
                return self.assignments[model_name]

            best_gpu: Optional[int] = None
            lowest_util = 101
            for gid, state in self.gpu_states.items():
                if state.free_memory_mb >= required_vram_mb and state.utilization_percent < lowest_util:
                    lowest_util = state.utilization_percent
                    best_gpu = gid

            if best_gpu is not None:
                self.assignments[model_name] = best_gpu
                logger.info(
                    "Modelo '%s' alocado na GPU %d (%s) — VRAM requerida: %dMB",
                    model_name, best_gpu, self.gpu_states[best_gpu].name, required_vram_mb
                )
            else:
                logger.error(
                    "Sem VRAM suficiente para modelo '%s' (%dMB)", model_name, required_vram_mb
                )
            return best_gpu

    def release_model(self, model_name: str):
        """Libera a GPU alocada para o modelo."""
        with self._lock:
            if model_name in self.assignments:
                gid = self.assignments.pop(model_name)
                logger.info("Modelo '%s' liberado da GPU %d.", model_name, gid)
            else:
                logger.warning("Tentativa de liberar modelo não alocado: '%s'.", model_name)

    def get_live_report(self) -> Dict[int, GpuState]:
        """Retorna cópia do estado atual de todas as GPUs."""
        with self._lock:
            return dict(self.gpu_states)

    def shutdown(self):
        """Finaliza thread de monitoramento e encerra NVML."""
        if self._monitor_thread:
            self._stop_event.set()
            self._monitor_thread.join()
            self._monitor_thread = None
            logger.info("Thread de monitoramento parada.")
        if self.is_initialized:
            nvmlShutdown()
            logger.info("NVML finalizada com sucesso.")


# Instância global para todo o aplicativo
_hardware_manager: Optional[HardwareManager] = None

def get_hardware_manager() -> HardwareManager:
    global _hardware_manager
    if _hardware_manager is None:
        _hardware_manager = HardwareManager()
    return _hardware_manager
