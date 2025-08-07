# -*- coding: utf-8 -*-
"""
Módulo Command Dispatcher (Despachante de Comandos)

Implementa um despachante que mapeia nomes de comandos para suas respectivas
funções de manipulador. Suporta handlers síncronos e assíncronos, desacoplando
o chamador da implementação do comando.
"""

import logging
import asyncio
import threading
from typing import Dict, Callable, Any, List, Union, Awaitable

from .health_manager import health_manager
from .hardware import get_hardware_manager
from .cache import cache

# Logger configurado para o módulo
logger = logging.getLogger(f"superezio_enterprise.{__name__}")

# Tipo para um handler que pode ser síncrono ou uma corotina
CommandHandler = Union[Callable[..., Any], Callable[..., Awaitable[Any]]]


class CommandDispatcher:
    """
    Despachante de comandos que registra e executa funções com base em um nome.
    Implementado como um singleton para fornecer um registro central de comandos.
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

        self._commands: Dict[str, CommandHandler] = {}
        self._initialized = True
        self._register_default_commands()
        logger.info("Command Dispatcher (Singleton) inicializado.")

    def _register_default_commands(self) -> None:
        """Registra os comandos padrão do sistema."""
        # Comandos assíncronos
        self.register("system:health_check", health_manager.get_health_status)

        # Comandos síncronos
        self.register("system:gpu_info", get_hardware_manager().get_live_report)
        self.register("system:cpu_usage", lambda: None)     # implementar se desejar com psutil
        self.register("system:memory_usage", lambda: None)  # implementar se desejar com psutil
        self.register("cache:clear_all", cache.clear)

    def register(self, command_name: str, handler: CommandHandler) -> None:
        """
        Registra um novo comando no despachante.
        """
        if command_name in self._commands:
            logger.warning("O comando '%s' está sendo sobrescrito.", command_name)
        self._commands[command_name] = handler
        logger.info(
            "Comando '%s' registrado com o handler '%s'. Async: %s",
            command_name,
            handler.__name__,
            asyncio.iscoroutinefunction(handler),
        )

    async def dispatch_async(self, command_name: str, *args, **kwargs) -> Any:
        """
        Localiza e executa um comando de forma assíncrona.
        Se o handler for síncrono, ele será executado em um executor para não bloquear o loop.
        """
        handler = self._get_handler(command_name)

        logger.info("Executando comando '%s' de forma assíncrona...", command_name)
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(*args, **kwargs)
            else:
                loop = asyncio.get_running_loop()
                result = await loop.run_in_executor(
                    None, lambda: handler(*args, **kwargs)
                )

            logger.info("Comando '%s' executado com sucesso.", command_name)
            return result
        except Exception:
            logger.error(
                "Exceção ao executar o comando '%s'.", command_name, exc_info=True
            )
            raise

    def dispatch_sync(self, command_name: str, *args, **kwargs) -> Any:
        """
        Localiza e executa um comando de forma síncrona.
        Lança um erro se o handler for uma corotina.
        """
        handler = self._get_handler(command_name)
        if asyncio.iscoroutinefunction(handler):
            raise TypeError(
                f"Não é possível executar o comando assíncrono '{command_name}' de forma síncrona."
            )

        logger.info("Executando comando '%s' de forma síncrona...", command_name)
        try:
            result = handler(*args, **kwargs)
            logger.info("Comando '%s' executado com sucesso.", command_name)
            return result
        except Exception:
            logger.error(
                "Exceção ao executar o comando '%s'.", command_name, exc_info=True
            )
            raise

    def _get_handler(self, command_name: str) -> CommandHandler:
        """Busca um handler no registro."""
        handler = self._commands.get(command_name)
        if not handler:
            logger.error("Comando desconhecido solicitado: '%s'", command_name)
            raise KeyError(f"O comando '{command_name}' não está registrado.")
        return handler

    def list_commands(self) -> List[str]:
        """Retorna uma lista com os nomes de todos os comandos registrados."""
        return sorted(self._commands.keys())


# Instância singleton do despachante de comandos
command_dispatcher = CommandDispatcher()
