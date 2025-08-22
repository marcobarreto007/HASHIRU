# -*- coding: utf-8 -*-
"""
Módulo de Correlação e Contexto

Gerencia o contexto da aplicação, incluindo IDs de correlação, IDs de sessão e
dados de usuário, usando ContextVars para garantir a segurança em ambientes
síncronos e assíncronos. Fornece um gerenciador de contexto para rastrear
operações de ponta a ponta.
"""

import uuid
import time
import logging
from contextvars import ContextVar
from typing import Optional, Dict, Any

# Logger configurado para o módulo. Ele herda a configuração do logger raiz.
logger = logging.getLogger(f"superezio_enterprise.{__name__}")

# --- ContextVars ---
# ContextVars são usados para armazenar dados que são específicos de um contexto de execução,
# como uma única requisição em um servidor web, sem a necessidade de passar os dados
# por todas as chamadas de função.

# ID de Correlação: Agrupa todas as operações de uma única tarefa/requisição.
correlation_id: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)

# ID de Sessão: Agrupa todas as requisições de um mesmo usuário.
session_id: ContextVar[Optional[str]] = ContextVar("session_id", default=None)

# Contexto do Usuário: Armazena dados arbitrários sobre o usuário logado.
user_context: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "user_context", default=None
)

# --- Funções de Gerenciamento de Contexto ---


def get_user_context() -> Dict[str, Any]:
    """
    Retorna o dicionário de contexto do usuário. Se não existir, cria um novo.
    """
    ctx = user_context.get()
    if ctx is None:
        ctx = {}
        user_context.set(ctx)
    return ctx


def set_context(
    corr_id: Optional[str] = None,
    sess_id: Optional[str] = None,
    u_context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Define os valores de correlação, sessão e contexto do usuário para o contexto atual.
    """
    if corr_id:
        correlation_id.set(corr_id)
        logger.debug(f"ID de Correlação definido como: {corr_id}")
    if sess_id:
        session_id.set(sess_id)
        logger.debug(f"ID de Sessão definido como: {sess_id}")
    if u_context:
        user_context.set(u_context)
        logger.debug(f"Contexto do usuário definido: {u_context}")


# --- Gerenciador de Contexto de Correlação ---


class CorrelationContext:
    """
    Um gerenciador de contexto assíncrono para rastrear a duração e o sucesso
    de uma operação específica, garantindo que ela tenha um ID de correlação.
    """

    def __init__(self, operation_name: str, existing_corr_id: Optional[str] = None):
        self.operation_name = operation_name
        self.token = None
        # Reutiliza um ID existente ou cria um novo
        self.corr_id = existing_corr_id or f"corr-{uuid.uuid4()}"
        self.start_time = 0.0

    async def __aenter__(self):
        """Inicia o contexto, define o ID de correlação e loga o início."""
        self.token = correlation_id.set(self.corr_id)
        self.start_time = time.monotonic()
        logger.info("Iniciando operação: '%s'", self.operation_name)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Finaliza o contexto, calcula a duração e loga o resultado (sucesso ou falha)."""
        duration_ms = (time.monotonic() - self.start_time) * 1000
        if exc_type:
            logger.error(
                "Falha na operação: '%s'. Duração: %.2f ms. Erro: %s",
                self.operation_name,
                duration_ms,
                exc_val,
                exc_info=(exc_type, exc_val, exc_tb),
            )
        else:
            logger.info(
                "Operação concluída com sucesso: '%s'. Duração: %.2f ms",
                self.operation_name,
                duration_ms,
            )
        correlation_id.reset(self.token)
