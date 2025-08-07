# -*- coding: utf-8 -*-
"""
Testes para o EnterpriseSessionManager (session_manager.py).
"""

import pytest
import time
from datetime import datetime, timezone

from superezio_enterprise.session_manager import EnterpriseSessionManager

@pytest.fixture
def manager_instance():
    """Fornece uma instância limpa do SessionManager para cada teste."""
    # Como é um singleton, precisamos garantir um estado limpo
    instance = EnterpriseSessionManager(session_ttl_seconds=1) # TTL curto para teste
    instance.sessions.clear()
    instance._last_activity_ts.clear()
    yield instance
    instance.sessions.clear()
    instance._last_activity_ts.clear()

def test_session_manager_singleton(manager_instance):
    """Testa se o EnterpriseSessionManager segue o padrão singleton."""
    instance1 = manager_instance
    instance2 = EnterpriseSessionManager()
    assert instance1 is instance2

def test_create_session(manager_instance):
    """Testa a criação de uma nova sessão."""
    session_id = manager_instance.create_session(user_id="user123")
    assert isinstance(session_id, str)
    assert session_id.startswith("sess-")

    session = manager_instance.get_session(session_id)
    assert session is not None
    assert session["user_id"] == "user123"
    assert "created_at" in session
    assert session["metrics"]["messages_sent"] == 0
    assert session["preferences"]["theme"] == "dark"

def test_create_session_with_initial_prefs(manager_instance):
    """Testa a criação de uma sessão com preferências iniciais."""
    prefs = {"theme": "light", "notifications": True}
    session_id = manager_instance.create_session(user_id="user456", initial_prefs=prefs)
    session = manager_instance.get_session(session_id)
    assert session["preferences"]["theme"] == "light"
    assert session["preferences"]["language"] == "pt-BR" # Padrão mantido
    assert session["preferences"]["notifications"] is True

def test_get_session_updates_activity(manager_instance):
    """Testa se a recuperação de uma sessão atualiza sua atividade."""
    session_id = manager_instance.create_session(user_id="user1")
    session1 = manager_instance.get_session(session_id)
    time.sleep(0.02)
    session2 = manager_instance.get_session(session_id)

    last_activity1 = session1["last_activity"]
    last_activity2 = session2["last_activity"]
    assert last_activity2 > last_activity1

def test_session_expiration(manager_instance):
    """Testa se uma sessão expira após o TTL de inatividade."""
    # TTL está configurado para 1 segundo no fixture
    session_id = manager_instance.create_session(user_id="user_exp")
    assert manager_instance.get_session(session_id) is not None

    time.sleep(1.1)

    assert manager_instance.get_session(session_id) is None
    assert session_id not in manager_instance.sessions

def test_invalidate_session(manager_instance):
    """Testa a invalidação manual de uma sessão."""
    session_id = manager_instance.create_session(user_id="user_inv")
    assert manager_instance.get_session(session_id) is not None

    manager_instance.invalidate_session(session_id)
    assert manager_instance.get_session(session_id) is None
    assert session_id not in manager_instance.sessions

def test_update_session_metric(manager_instance):
    """Testa a atualização de métricas de uma sessão."""
    session_id = manager_instance.create_session(user_id="user_metric")

    success = manager_instance.update_session_metric(session_id, "messages_sent", 5)
    assert success is True

    success = manager_instance.update_session_metric(session_id, "commands_executed")
    assert success is True

    session = manager_instance.get_session(session_id)
    assert session["metrics"]["messages_sent"] == 5
    assert session["metrics"]["commands_executed"] == 1
    assert session["metrics"]["errors_encountered"] == 0

def test_update_metric_on_invalid_session(manager_instance):
    """Testa se a atualização de métrica falha para uma sessão inválida."""
    success = manager_instance.update_session_metric("invalid-id", "messages_sent")
    assert success is False
