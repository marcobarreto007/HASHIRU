# -*- coding: utf-8 -*-
"""
Módulo Enterprise Session Manager

Gerencia o ciclo de vida das sessões de usuário de forma robusta e thread-safe.
Armazena dados detalhados da sessão, incluindo contexto, métricas de uso e
preferências do usuário, com expiração baseada em inatividade.
"""

import uuid
import time
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Literal


# Logger configurado para o módulo
logger = logging.getLogger(f"superezio_enterprise.{__name__}")

# Define os tipos de métricas para validação
SessionMetric = Literal["messages_sent", "commands_executed", "errors_encountered"]


class EnterpriseSessionManager:
    """
    Gerenciador de sessões em memória, implementado como um singleton thread-safe.

    As sessões mantêm o estado do usuário e expiram após um período de inatividade
    configurável (session_ttl_seconds). Cada sessão contém metadados, contexto,
    métricas de interação e preferências do usuário.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, session_ttl_seconds: int = 1800):  # 30 minutos
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._last_activity_ts: Dict[str, float] = {}
        self.session_ttl = session_ttl_seconds
        self._lock = threading.RLock()
        self._initialized = True
        logger.info(
            "EnterpriseSessionManager (Singleton) inicializado com TTL de %ds.",
            self.session_ttl,
        )

    def create_session(self, user_id: str, initial_prefs: Optional[Dict] = None) -> str:
        """
        Cria uma nova sessão para um usuário e retorna o ID da sessão.
        """
        session_id = f"sess-{uuid.uuid4()}"
        now = datetime.now(timezone.utc)
        with self._lock:
            self.sessions[session_id] = {
                "user_id": user_id,
                "created_at": now,
                "last_activity": now,
                "context": {},
                "metrics": {
                    "messages_sent": 0,
                    "commands_executed": 0,
                    "errors_encountered": 0,
                },
                "preferences": {
                    "theme": "dark",
                    "language": "pt-BR",
                    **(initial_prefs or {}),
                },
            }
            self._last_activity_ts[session_id] = time.monotonic()
        logger.info("Sessão criada: %s para o usuário '%s'.", session_id, user_id)
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupera uma sessão se ela existir e não tiver expirado devido à inatividade.
        Atualiza o timestamp de última atividade da sessão.
        """
        if not session_id:
            return None

        with self._lock:
            if session_id not in self.sessions:
                return None

            # Verifica a expiração por inatividade
            if (
                time.monotonic() - self._last_activity_ts.get(session_id, 0)
                > self.session_ttl
            ):
                logger.warning("Sessão %s expirou devido à inatividade.", session_id)
                self.invalidate_session(session_id)
                return None

            # Atualiza a atividade
            self.sessions[session_id]["last_activity"] = datetime.now(timezone.utc)
            self._last_activity_ts[session_id] = time.monotonic()
            logger.debug("Sessão %s acessada com sucesso.", session_id)
            return self.sessions[session_id]

    def update_session_metric(
        self, session_id: str, metric: SessionMetric, increment: int = 1
    ) -> bool:
        """
        Atualiza uma métrica específica dentro de uma sessão válida.
        """
        with self._lock:
            session = self.get_session(session_id)
            if session and metric in session["metrics"]:
                session["metrics"][metric] += increment
                logger.debug(
                    "Métrica '%s' na sessão %s atualizada para %d.",
                    metric,
                    session_id,
                    session["metrics"][metric],
                )
                return True
            elif session:
                logger.warning(
                    "Métrica desconhecida '%s' para a sessão %s.", metric, session_id
                )
            return False

    def invalidate_session(self, session_id: str) -> None:
        """Remove uma sessão do gerenciador."""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                del self._last_activity_ts[session_id]
                logger.info("Sessão %s foi invalidada e removida.", session_id)


# --- Instância Global ---
# A instância singleton do EnterpriseSessionManager que será usada em toda a aplicação.
session_manager = EnterpriseSessionManager()
