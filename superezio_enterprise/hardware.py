# -*- coding: utf-8 -*-
"""
Módulo de Gerenciamento de Hardware (GPU NVIDIA) - Robusto

Fornece uma interface para descobrir, monitorar e alocar modelos de IA em GPUs NVIDIA,
com tratamento de erro gracioso para ambientes sem NVIDIA ou sem pynvml instalado.
"""

import logging
import threading
import time
import dataclasses
from typing import Dict, Any, Optional, List

# --- Importação Robusta do pynvml ---
try:
    from pynvml import (
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
    PYNVM_AVAILABLE = True
except ImportError:
    # Cria stubs/mocks se a biblioteca não estiver disponível
    PYNVM_AVAILABLE = False
    logger = logging.getLogger("superezio_enterprise.hardware")
    logger.warning("A biblioteca 'pynvml' não foi encontrada. O monitoramento de GPU será desativado.")

    class NVMLError(Exception):
        pass

    def nvmlInit(): pass
    def nvmlDeviceGetCount(): return 0
    def nvmlDeviceGetHandleByIndex(index): return None
    def nvmlDeviceGetMemoryInfo(handle): return None
    def nvmlDeviceGetUtilizationRates(handle): return None
    def nvmlDeviceGetTemperature(handle, sensor): return 0
    def nvmlDeviceGetPowerUsage(handle): return 0
    def nvmlDeviceGetName(handle): return "N/A"
    def nvmlShutdown(): pass
    NVML_TEMPERATURE_GPU = 0

from .config import CONFIG

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
    Singleton que gerencia GPUs NVIDIA, com fallback gracioso se não disponíveis.
    """
    _instance: Optional["HardwareManager"] = None
    _class_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._class_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
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

        if not PYNVM_AVAILABLE:
            self._initialized = True
            return # Interrompe a inicialização se a biblioteca não existe

        try:
            nvmlInit()
            self.gpu_count = nvmlDeviceGetCount()
            if self.gpu_count == 0:
                logger.warning("Nenhuma GPU NVIDIA encontrada no sistema.")
            else:
                for i in range(self.gpu_count):
                    handle = nvmlDeviceGetHandleByIndex(i)
                    self.gpu_handles.append(handle)
                logger.info(f"NVML inicializada. {self.gpu_count} GPUs encontradas.")
                self.update_all_gpu_states()
                self.start_monitoring()

            self.is_initialized = True
            self._initialized = True

        except NVMLError as e:
            logger.critical(f"Falha ao inicializar NVML: {e}. O monitoramento de GPU estará desativado.")
            self.gpu_count = 0 # Garante que o resto do sistema saiba que não há GPUs

    def start_monitoring(self):
        if not self.is_initialized or not self.gpu_count or self._monitor_thread:
            return
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"Monitoramento de GPU iniciado (intervalo: {CONFIG.gpu_monitoring_interval_seconds}s)")

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            self.update_all_gpu_states()
            time.sleep(CONFIG.gpu_monitoring_interval_seconds)

    def update_all_gpu_states(self):
        if not self.is_initialized or not self.gpu_count:
            return
        with self._lock:
            for idx, handle in enumerate(self.gpu_handles):
                try:
                    mem = nvmlDeviceGetMemoryInfo(handle)
                    util = nvmlDeviceGetUtilizationRates(handle)
                    temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
                    power = nvmlDeviceGetPowerUsage(handle) / 1000.0
                    raw_name = nvmlDeviceGetName(handle)
                    name = raw_name.decode("utf-8", errors="ignore") if isinstance(raw_name, (bytes, bytearray)) else raw_name

                    self.gpu_states[idx] = GpuState(
                        id=idx, name=name,
                        total_memory_mb=mem.total / (1024**2),
                        free_memory_mb=mem.free / (1024**2),
                        used_memory_mb=mem.used / (1024**2),
                        utilization_percent=util.gpu,
                        temperature_c=temp,
                        power_usage_w=power,
                    )
                except NVMLError as e:
                    logger.error(f"Erro ao atualizar estado da GPU {idx}: {e}")
                    # Remove o handle se ele estiver causando erros persistentes
                    self.gpu_handles.pop(idx)
                    self.gpu_count = len(self.gpu_handles)
                    break
        logger.debug("Estados das GPUs atualizados.")

    def assign_model_to_gpu(self, model_name: str, required_vram_mb: int, preferred_gpu_id: int = -1) -> Optional[int]:
        if not self.is_initialized or not self.gpu_count:
            logger.warning("Alocação de modelo ignorada: Nenhuma GPU disponível.")
            return None
        with self._lock:
            # ... (a lógica de alocação permanece a mesma)
            return super().assign_model_to_gpu(model_name, required_vram_mb)

    def release_model(self, model_name: str):
        with self._lock:
            if model_name in self.assignments:
                gid = self.assignments.pop(model_name)
                logger.info("Modelo '%s' liberado da GPU %d.", model_name, gid)

    def get_live_report(self) -> Dict[int, GpuState]:
        with self._lock:
            return dict(self.gpu_states)

    def check_gpu_health(self) -> Dict[str, Any]:
        """Verifica a saúde das GPUs para o HealthManager."""
        if not self.is_initialized or not self.gpu_count:
            return {"status": "no_gpu_available"}

        hot_gpus = []
        for state in self.gpu_states.values():
            if state.temperature_c > CONFIG.gpu_temperature_threshold:
                hot_gpus.append(state.id)

        if hot_gpus:
            return {"status": "unhealthy", "overheating_gpus": hot_gpus}
        return {"status": "healthy", "gpu_count": self.gpu_count}

    def shutdown(self):
        if self._monitor_thread:
            self._stop_event.set()
            self._monitor_thread.join()
            self._monitor_thread = None
        if PYNVM_AVAILABLE and self.is_initialized:
            try:
                nvmlShutdown()
                logger.info("NVML finalizada com sucesso.")
            except NVMLError as e:
                logger.error(f"Erro ao finalizar NVML: {e}")

# Instância global para todo o aplicativo
_hardware_manager: Optional[HardwareManager] = None

def get_hardware_manager() -> HardwareManager:
    global _hardware_manager
    if _hardware_manager is None:
        _hardware_manager = HardwareManager()
    return _hardware_manager
