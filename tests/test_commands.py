# -*- coding: utf-8 -*-
"""
Testes para o Command Dispatcher (commands.py).
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch

from superezio_enterprise.commands import CommandDispatcher

# Mock para handlers síncronos e assíncronos
def sync_handler(arg1, kwarg1=None):
    """Um handler síncrono de exemplo."""
    return f"sync: {arg1}, {kwarg1}"

async def async_handler(arg1, kwarg1=None):
    """Um handler assíncrono de exemplo."""
    await asyncio.sleep(0.01)
    return f"async: {arg1}, {kwarg1}"

@pytest.fixture
def dispatcher():
    """Fornece uma instância limpa do CommandDispatcher para cada teste."""
    # O CommandDispatcher é um singleton, então precisamos resetar seu estado
    instance = CommandDispatcher()
    instance._commands = {}  # Limpa os comandos registrados
    instance._register_default_commands() # Registra os comandos padrão novamente
    return instance

def test_dispatcher_singleton(dispatcher):
    """Testa se o CommandDispatcher segue o padrão singleton."""
    instance1 = dispatcher
    instance2 = CommandDispatcher()
    assert instance1 is instance2

def test_register_command(dispatcher):
    """Testa o registro de um novo comando."""
    assert "test:sync" not in dispatcher.list_commands()
    dispatcher.register("test:sync", sync_handler)
    assert "test:sync" in dispatcher.list_commands()

def test_register_overwrite_warning(dispatcher, caplog):
    """Testa se um aviso é emitido ao sobrescrever um comando."""
    dispatcher.register("test:overwrite", sync_handler)
    with caplog.at_level("WARNING"):
        dispatcher.register("test:overwrite", async_handler)
    assert "está sendo sobrescrito" in caplog.text

@pytest.mark.asyncio
async def test_dispatch_async_with_async_handler(dispatcher):
    """Testa a execução assíncrona de um handler assíncrono."""
    dispatcher.register("test:async", async_handler)
    result = await dispatcher.dispatch_async("test:async", "hello", kwarg1="world")
    assert result == "async: hello, world"

@pytest.mark.asyncio
async def test_dispatch_async_with_sync_handler(dispatcher):
    """Testa a execução assíncrona de um handler síncrono (via executor)."""
    dispatcher.register("test:sync", sync_handler)
    result = await dispatcher.dispatch_async("test:sync", "hello", kwarg1="world")
    assert result == "sync: hello, world"

def test_dispatch_sync_with_sync_handler(dispatcher):
    """Testa a execução síncrona de um handler síncrono."""
    dispatcher.register("test:sync", sync_handler)
    result = dispatcher.dispatch_sync("test:sync", "hello", kwarg1="world")
    assert result == "sync: hello, world"

def test_dispatch_sync_with_async_handler_raises_error(dispatcher):
    """Testa se a execução síncrona de um handler assíncrono levanta um TypeError."""
    dispatcher.register("test:async", async_handler)
    with pytest.raises(TypeError, match="Não é possível executar o comando assíncrono"):
        dispatcher.dispatch_sync("test:async", "hello")

@pytest.mark.asyncio
async def test_dispatch_unknown_command_raises_error(dispatcher):
    """Testa se a tentativa de despachar um comando desconhecido levanta KeyError."""
    with pytest.raises(KeyError, match="não está registrado"):
        await dispatcher.dispatch_async("test:nonexistent")

    with pytest.raises(KeyError, match="não está registrado"):
        dispatcher.dispatch_sync("test:nonexistent")

def test_list_commands(dispatcher):
    """Testa a listagem de comandos registrados."""
    dispatcher.register("cmd:b", sync_handler)
    dispatcher.register("cmd:a", async_handler)
    # Os comandos padrão também devem estar na lista
    commands = dispatcher.list_commands()
    assert isinstance(commands, list)
    assert "cmd:a" in commands
    assert "cmd:b" in commands
    assert "system:health_check" in commands # Comando padrão
    assert commands == sorted(commands)  # Garante que a lista está ordenada
