# -*- coding: utf-8 -*-
"""
Módulo de Configuração de Logging Enterprise

Configura um sistema de logging assíncrono e estruturado, utilizando uma fila
para evitar bloqueios de I/O. Inclui filtros para adicionar IDs de correlação
e sessão a todos os registros de log, facilitando o rastreamento.
"""

import logging
import json
import queue
from logging.handlers import QueueHandler, QueueListener, RotatingFileHandler

# Importa a configuração e os ContextVars de outros módulos do projeto
from .config import CONFIG
from .correlation import correlation_id, session_id


class CorrelationFilter(logging.Filter):
    """
    Filtro de log que injeta o ID de correlação e o ID de sessão em cada registro.
    Obtém os valores dos ContextVars, garantindo que sejam específicos do contexto.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.correlation_id = correlation_id.get() or "no-correlation-id"
        record.session_id = session_id.get() or "no-session-id"
        # Adiciona o nome do módulo de forma explícita para o formatador
        record.module_name = record.name
        return True


class StructuredFormatter(logging.Formatter):
    """
    Formatador de log que converte o registro de log em uma string JSON.
    Inclui campos estruturados para fácil análise por sistemas de monitoramento.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module_name,
            "correlation_id": record.correlation_id,
            "session_id": record.session_id,
            "thread_id": record.thread,
            "process_id": record.process,
        }
        # Adiciona informações de exceção, se presentes
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_enterprise_logging() -> logging.Logger:
    """
    Configura e inicializa o sistema de logging da aplicação.

    - Usa uma Queue para fazer o logging de forma assíncrona.
    - Configura um RotatingFileHandler para salvar logs em arquivos com rotação.
    - Configura um StreamHandler para exibir logs no console.
    - Aplica o formatador estruturado (JSON) se habilitado na configuração.
    - Adiciona o filtro de correlação a todos os logs.

    Returns:
        A instância do logger principal da aplicação.
    """
    log_queue = queue.Queue(-1)  # Fila de tamanho infinito

    # O handler principal apenas coloca os logs na fila
    queue_handler = QueueHandler(log_queue)
    queue_handler.addFilter(CorrelationFilter())

    # Handler para escrever os logs em um arquivo rotativo
    file_handler = RotatingFileHandler(
        filename="superezio_enterprise.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,  # Mantém 5 arquivos de backup
        encoding="utf-8",
    )

    # Handler para exibir logs no console
    console_handler = logging.StreamHandler()

    # Aplica o formatador apropriado aos handlers de destino
    if CONFIG.structured_logging:
        formatter = StructuredFormatter()
    else:
        # Fallback para um formato de texto simples se o log estruturado estiver desabilitado
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(module_name)s] - [%(correlation_id)s] - %(message)s"
        )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # O listener escuta a fila e envia os logs para os handlers de destino
    listener = QueueListener(
        log_queue, file_handler, console_handler, respect_handler_level=True
    )
    listener.start()

    # Configura o logger raiz da aplicação
    logger = logging.getLogger("superezio_enterprise")
    logger.setLevel(getattr(logging, CONFIG.log_level.upper(), logging.INFO))
    logger.addHandler(queue_handler)

    # Garante que o listener seja parado corretamente ao final da aplicação
    import atexit

    atexit.register(listener.stop)

    logger.info(
        "Logging Enterprise configurado com sucesso. Modo estruturado: %s",
        CONFIG.structured_logging,
    )

    return logger
