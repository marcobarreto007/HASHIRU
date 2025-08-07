# -*- coding: utf-8 -*-
# tools/automation_wrapper.py - Wrapper para compatibilidade

def handle_automation_command(command: str, args: str = "") -> str:
    """
    Wrapper que converte Dict results do automation_commands original para string.
    Compatible com main_agent.py expectations.
    """
    
    try:
        # Import original automation_commands (que retorna Dict)
        from tools import automation_commands as original_ac
        
        # Call original function
        result = original_ac.handle_automation_command(command, args)
        
        # Convert Dict to String
        if isinstance(result, dict):
            if "error" in result:
                return f"❌ **Erro:** {result['error']}"
            elif "success" in result and result["success"]:
                return result.get("message", "✅ Comando executado com sucesso")
            else:
                return str(result)
        else:
            # Already string
            return str(result)
            
    except Exception as e:
        return f"❌ **Erro no wrapper de automação:** {str(e)[:100]}..."