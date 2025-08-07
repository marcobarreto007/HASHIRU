# agent_structs.py
# -*- coding: utf-8 -*-
"""
Este arquivo define as estruturas de dados (dataclasses) usadas pelo agente.
"""
from dataclasses import dataclass

@dataclass
class Task:
    """Representa uma tarefa identificada para o agente executar."""
    task_type: str
    summary: str
    user_input: str
    is_direct_command: bool = False