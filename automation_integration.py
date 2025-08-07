# -*- coding: utf-8 -*-
"""
HASHIRU 6.1 - INTEGRAÇÃO DE AUTOMAÇÃO
Adicione este código ao seu tools/__init__.py ou main_agent.py
"""

from tools.automation_master import AUTOMATION_COMMANDS

# Integrar comandos de automação ao sistema principal
def register_automation_commands():
    """Registrar todos os comandos de automação"""
    return AUTOMATION_COMMANDS

# Exemplo de uso no main_agent.py:
"""
from tools.automation_master import get_automation_master

# No seu handler de comandos, adicione:
if command.startswith("/auto_"):
    automation_master = get_automation_master()
    
    if command == "/auto_search":
        result = automation_master.search_and_analyze(args)
    elif command == "/auto_browse":
        result = automation_master.navigate_to(args)
    elif command == "/auto_research":
        result = automation_master.auto_research_and_save(args)
    # ... etc
    
    return result
"""
