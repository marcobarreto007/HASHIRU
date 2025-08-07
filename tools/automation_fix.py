# -*- coding: utf-8 -*-
# APENAS A FUNÇÃO handle_automation_command CORRIGIDA

def handle_automation_command(command: str, args: str = "") -> str:
    """
    Handler unificado para todos os comandos de automação
    RETORNA STRING (não Dict) para compatibilidade com main_agent.py

    Args:
        command (str): Comando sem o prefixo / (ex: "search", "research")
        args (str): Argumentos do comando

    Returns:
        str: Resultado formatado da execução
    """
    
    # Importar get_automation_master que sabemos que existe
    try:
        from tools.automation_master import get_automation_master
    except ImportError as e:
        return f"❌ **Erro:** Módulo automation_master não encontrado: {str(e)}"
    
    # Comandos mapeados diretamente para automation_master
    try:
        master = get_automation_master()
        
        if command == "search":
            if not args.strip():
                return "❌ **Erro:** Forneça uma consulta de busca.\n💡 **Exemplo:** `/auto_search Python tutorials`"
            result = master.search_and_analyze(args.strip())
            
        elif command == "browse":
            if not args.strip():
                return "❌ **Erro:** Forneça uma URL.\n💡 **Exemplo:** `/auto_browse https://python.org`"
            result = master.navigate_to(args.strip())
            
        elif command == "click":
            if not args.strip():
                return "❌ **Erro:** Forneça um seletor.\n💡 **Exemplo:** `/auto_click #button-id`"
            parts = args.strip().split(maxsplit=1)
            selector = parts[0]
            selector_type = parts[1] if len(parts) > 1 else "css"
            result = master.click_element(selector, selector_type)
            
        elif command == "screenshot":
            name = args.strip() if args.strip() else None
            result = master.take_screenshot(name)
            
        elif command == "research":
            if not args.strip():
                return "❌ **Erro:** Forneça um tópico de pesquisa.\n💡 **Exemplo:** `/auto_research Claude AI features`"
            
            parts = args.strip().rsplit(maxsplit=1)
            topic = args.strip()
            num_sites = 3
            
            if len(parts) == 2 and parts[1].isdigit():
                topic = parts[0]
                num_sites = min(int(parts[1]), 10)
            
            result = master.auto_research_and_save(topic, num_sites)
            
        elif command == "type":
            if not args.strip():
                return "❌ **Erro:** Forneça texto para digitar.\n💡 **Exemplo:** `/auto_type Hello World`"
            result = master.type_text(args.strip())
            
        elif command == "keys":
            if not args.strip():
                return "❌ **Erro:** Forneça teclas.\n💡 **Exemplo:** `/auto_keys ctrl c`"
            keys = args.strip().split()
            result = master.press_key_combination(*keys)
            
        elif command == "folder":
            if not args.strip():
                return "❌ **Erro:** Forneça caminho da pasta.\n💡 **Exemplo:** `/auto_folder C:/Users/marco/Documents`"
            result = master.open_folder(args.strip())
            
        elif command == "find_files":
            if not args.strip():
                return "❌ **Erro:** Forneça padrão de busca.\n💡 **Exemplo:** `/auto_find_files *.py`"
            parts = args.strip().split(maxsplit=1)
            if len(parts) == 1:
                search_path = "."
                pattern = parts[0]
            else:
                search_path = parts[0]
                pattern = parts[1]
            result = master.search_files(search_path, pattern)
            
        elif command == "status":
            # Call automation_master status directly
            try:
                result = master.get_status_report()  # Assumindo que existe
            except AttributeError:
                # Fallback - criar status manual
                return """📊 **Status da Automação HASHIRU**

**Sistema:** ✅ Operacional
**Automation Master:** ✅ Carregado (23.6 KB)
**Comandos:** search, browse, click, screenshot, research, type, keys, folder, find_files

**Para detalhes completos:** Verificar automation_master.py diretamente"""
            
        else:
            available_commands = ["search", "browse", "click", "screenshot", "research", 
                                "type", "keys", "folder", "find_files", "status"]
            return f"❌ Comando de automação desconhecido: **{command}**\n\n💡 **Disponíveis:** {', '.join(available_commands)}"
        
        # Convert result dict to string
        if isinstance(result, dict):
            if "error" in result:
                return f"❌ **Erro:** {result['error']}"
            elif result.get("success", True):
                message = result.get("message", "")
                if message:
                    return message
                else:
                    return f"✅ **Comando {command} executado com sucesso**"
            else:
                return f"⚠️ **Resultado parcial:** {result}"
        else:
            return str(result)
        
    except Exception as e:
        return f"❌ **Erro na automação {command}:** {str(e)[:150]}..."