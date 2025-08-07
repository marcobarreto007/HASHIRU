# -*- coding: utf-8 -*-
"""
Testes para o HardwareManager (hardware.py).

Estes testes usam mocks para simular a biblioteca pynvml, permitindo
testar a lógica do HardwareManager sem a necessidade de uma GPU física.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from superezio_enterprise.hardware import HardwareManager, GpuState, get_hardware_manager

# Mock da pynvml antes de importar o módulo de hardware
# Isso garante que o HardwareManager use nossa versão mockada durante a inicialização
nvml_mock = MagicMock()

# Mock das constantes e funções da pynvml
nvml_mock.NVML_TEMPERATURE_GPU = 0
def nvml_error(*args, **kwargs):
    raise nvml_mock.NVMLError(1)

# Simula a estrutura de informações de memória
@pytest.fixture
def mock_nvml_structs():
    class MockMemInfo:
        def __init__(self, total, free, used):
            self.total = total
            self.free = free
            self.used = used

    class MockUtilRates:
        def __init__(self, gpu):
            self.gpu = gpu

    return MockMemInfo, MockUtilRates

@pytest.fixture
def mock_pynvml(mock_nvml_structs):
    """Configura o mock completo da pynvml para simular 2 GPUs."""
    MockMemInfo, MockUtilRates = mock_nvml_structs

    nvml_mock.reset_mock()
    nvml_mock.nvmlInit.side_effect = None
    nvml_mock.nvmlDeviceGetCount.return_value = 2

    # Configuração para GPU 0
    handle0 = "handle0"
    # Configuração para GPU 1
    handle1 = "handle1"

    nvml_mock.nvmlDeviceGetHandleByIndex.side_effect = [handle0, handle1]
    nvml_mock.nvmlDeviceGetName.side_effect = [
        b"Mock GPU 0",
        b"Mock GPU 1",
    ]
    nvml_mock.nvmlDeviceGetMemoryInfo.side_effect = [
        MockMemInfo(total=8000 * 1024**2, free=6000 * 1024**2, used=2000 * 1024**2),
        MockMemInfo(total=16000 * 1024**2, free=12000 * 1024**2, used=4000 * 1024**2),
    ]
    nvml_mock.nvmlDeviceGetUtilizationRates.side_effect = [
        MockUtilRates(gpu=10),
        MockUtilRates(gpu=50),
    ]
    nvml_mock.nvmlDeviceGetTemperature.return_value = 60
    nvml_mock.nvmlDeviceGetPowerUsage.return_value = 150 * 1000 # Em mW

    with patch.dict("sys.modules", {"pynvml": nvml_mock}):
        # Importa o módulo aqui para que ele use o mock
        from superezio_enterprise.hardware import HardwareManager, GpuState, get_hardware_manager
        nvml_mock.reset_mock()
        yield nvml_mock, HardwareManager, GpuState, get_hardware_manager

def test_hardware_manager_initialization(mock_pynvml):
    """Testa se o manager inicializa corretamente com as GPUs mockadas."""
    nvml, HardwareManager, _, get_hardware_manager_func = mock_pynvml
    HardwareManager._instance = None
    manager = get_hardware_manager_func()
    manager.shutdown() # Para a thread de monitoramento

    nvml.nvmlInit.assert_called_once()
    assert manager.is_initialized is True
    assert manager.gpu_count == 2
    assert len(manager.gpu_states) == 2
    assert manager.gpu_states[0].name == "Mock GPU 0"
    assert manager.gpu_states[1].total_memory_mb == pytest.approx(16000)

def test_assign_model_to_best_gpu(mock_pynvml):
    """Testa a lógica de alocação de modelo para a melhor GPU disponível."""
    _, HardwareManager, _, get_hardware_manager_func = mock_pynvml
    manager = get_hardware_manager_func()

    # Este modelo requer 5000 MB. Ambas as GPUs têm VRAM livre.
    # A GPU 0 tem menor utilização (10% vs 50%), então deve ser escolhida.
    assigned_gpu = manager.assign_model_to_gpu("model-a", 5000)
    assert assigned_gpu == 0
    assert manager.assignments["model-a"] == 0

    # Este modelo requer 10000 MB. Apenas a GPU 1 tem VRAM livre suficiente.
    assigned_gpu_2 = manager.assign_model_to_gpu("model-b", 10000)
    assert assigned_gpu_2 == 1
    assert manager.assignments["model-b"] == 1

    manager.shutdown()

def test_assign_model_insufficient_vram(mock_pynvml):
    """Testa a falha na alocação quando nenhuma GPU tem VRAM suficiente."""
    _, HardwareManager, _, get_hardware_manager_func = mock_pynvml
    manager = get_hardware_manager_func()
    assigned_gpu = manager.assign_model_to_gpu("huge-model", 20000)
    assert assigned_gpu is None
    manager.shutdown()

def test_release_model(mock_pynvml):
    """Testa a liberação de um modelo previamente alocado."""
    _, HardwareManager, _, get_hardware_manager_func = mock_pynvml
    manager = get_hardware_manager_func()
    manager.assign_model_to_gpu("model-c", 4000)
    assert "model-c" in manager.assignments

    manager.release_model("model-c")
    assert "model-c" not in manager.assignments
    manager.shutdown()

def test_initialization_fails_with_nvml_error(mock_pynvml):
    """Testa se o manager lida com erros de inicialização da NVML."""
    nvml, HardwareManager, _ = mock_pynvml
    nvml.nvmlInit.side_effect = nvml_mock.NVMLError(1)

    # Força a recriação da instância
    HardwareManager._instance = None
    manager = HardwareManager()

    assert manager.is_initialized is False
    assert manager.gpu_count == 0
    manager.shutdown()
