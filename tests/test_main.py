# -*- coding: utf-8 -*-
"""
Testes para o ponto de entrada principal (main.py).

Estes são testes de integração de alto nível (smoke tests) que garantem
que a aplicação pode ser inicializada e que o fluxo principal pode ser
executado sem erros, usando mocks para os componentes externos.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

# Mock do hardware_manager para evitar dependência de GPU real
@pytest.fixture
def mock_hardware():
    mock = MagicMock()
    mock.is_initialized = True
    mock.get_live_report.return_value = {
        0: MagicMock(name="Mock GPU 0", temperature_c=50, utilization_percent=10, used_memory_mb=100, total_memory_mb=8000, free_memory_mb=7900)
    }
    mock.assign_model_to_gpu.return_value = 0
    return mock

# Mock do session_manager
@pytest.fixture
def mock_session():
    mock = MagicMock()
    mock.create_session.return_value = "mock-session-id"
    return mock

# Mock do command_dispatcher
@pytest.fixture
def mock_dispatcher():
    mock = MagicMock()
    # O dispatch_async retorna um Awaitable (Future)
    future = asyncio.Future()
    future.set_result({"status": "ok"})
    mock.dispatch_async.return_value = future
    return mock

@pytest.mark.asyncio
@patch('superezio_enterprise.main.hardware_manager')
@patch('superezio_enterprise.main.session_manager')
@patch('superezio_enterprise.main.command_dispatcher')
@patch('superezio_enterprise.main.setup_enterprise_logging')
async def test_main_execution_flow(
    mock_setup_logging, mock_dispatcher_main, mock_session_main, mock_hardware_main, 
    mock_hardware, mock_session, mock_dispatcher
):
    """Testa o fluxo de execução da função main, garantindo as chamadas esperadas."""
    # Associa os mocks dos fixtures aos patches do main
    mock_hardware_main.return_value = mock_hardware
    mock_session_main.return_value = mock_session
    mock_dispatcher_main.return_value = mock_dispatcher

    # Importa o main aqui para que ele use os mocks
    from superezio_enterprise import main

    # Reduz o tempo de sleep para acelerar o teste
    with patch('asyncio.sleep', new_callable=AsyncMock):
        await main.main()

    # Verifica se as funções chave foram chamadas
    mock_setup_logging.assert_called_once()
    mock_session.create_session.assert_called_once_with(user_id="gpu_test_user")
    
    # Verifica se a alocação de modelos foi tentada
    assert mock_hardware.assign_model_to_gpu.call_count >= 1
    mock_hardware.assign_model_to_gpu.assert_any_call(
        "large-language-model-v1", required_vram_mb=8000
    )

    # Verifica se o monitoramento foi chamado
    assert mock_hardware.get_live_report.call_count > 0

    # Verifica se a liberação foi chamada
    mock_hardware.release_model.assert_any_call("large-language-model-v1")

    # Verifica se o health check foi chamado no final
    mock_dispatcher.dispatch_async.assert_called_once_with("system:health_check")

    # Verifica se o shutdown foi chamado para limpar os recursos
    mock_hardware.shutdown.assert_called_once()
