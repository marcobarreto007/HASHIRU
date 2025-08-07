# -*- coding: utf-8 -*-
"""
HASHIRU 6.1 - COMANDOS DE AUTOMAÇÃO INTEGRADOS (CORRIGIDO)
Comandos simples para usar com Chainlit - SEM UNICODE ERRORS
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from tools.automation_master import get_automation_master

def handle_auto_search(args: str) -> Dict[str, Any]:
    """
    Buscar na internet e analisar resultados
    Uso: /auto_search machine learning Python
    """
    if not args.strip():
        return {"error": "Forneça uma consulta de busca. Exemplo: /auto_search Python programming"}
    
    master = get_automation_master()
    result = master.search_and_analyze(args.strip())
    
    if "error" in result:
        return result
    
    # Formatar resposta para o usuário
    response = f"🔍 **Busca por:** {result['query']}\n\n"
    response += f"📊 **{len(result['results'])} resultados encontrados:**\n\n"
    
    for i, res in enumerate(result['results'][:5], 1):
        response += f"**{i}. {res['title']}**\n"
        response += f"🌐 {res['url']}\n"
        response += f"📝 {res['snippet'][:150]}...\n\n"
    
    return {
        "success": True,
        "message": response,
        "data": result
    }

def handle_auto_browse(args: str) -> Dict[str, Any]:
    """
    Navegar para URL específica
    Uso: /auto_browse https://python.org
    """
    if not args.strip():
        return {"error": "Forneça uma URL. Exemplo: /auto_browse https://python.org"}
    
    master = get_automation_master()
    result = master.navigate_to(args.strip())
    
    if "error" in result:
        return result
    
    response = f"🌐 **Navegou para:** {result['url']}\n"
    response += f"📄 **Título:** {result['title']}\n"
    response += f"✅ **Status:** Página carregada com sucesso"
    
    return {
        "success": True,
        "message": response,
        "data": result
    }

def handle_auto_click(args: str) -> Dict[str, Any]:
    """
    Clicar em elemento da página
    Uso: /auto_click #search-button
    Uso: /auto_click //button[@type='submit'] xpath
    """
    parts = args.strip().split(maxsplit=1)
    if not parts:
        return {"error": "Forneça um seletor. Exemplo: /auto_click #search-button"}
    
    selector = parts[0]
    selector_type = parts[1] if len(parts) > 1 else "css"
    
    master = get_automation_master()
    result = master.click_element(selector, selector_type)
    
    if "error" in result:
        return result
    
    response = f"🖱️ **Clique realizado!**\n"
    response += f"🎯 **Seletor:** {selector} ({selector_type})\n"
    if result.get("element_text"):
        response += f"📝 **Texto do elemento:** {result['element_text']}"
    
    return {
        "success": True,
        "message": response,
        "data": result
    }

def handle_auto_screenshot(args: str = None) -> Dict[str, Any]:
    """
    Capturar screenshot da tela
    Uso: /auto_screenshot
    Uso: /auto_screenshot minha_captura
    """
    name = args.strip() if args and args.strip() else None
    
    master = get_automation_master()
    result = master.take_screenshot(name)
    
    if "error" in result:
        return result
    
    response = f"📸 **Screenshot capturado!**\n"
    response += f"💾 **Arquivo:** {result['filepath']}\n"
    response += f"📏 **Tamanho:** {result['size'][0]}x{result['size'][1]} pixels"
    
    return {
        "success": True,
        "message": response,
        "data": result
    }

def handle_auto_research(args: str) -> Dict[str, Any]:
    """
    Pesquisa completa: buscar + navegar + analisar + salvar
    Uso: /auto_research artificial intelligence
    Uso: /auto_research "machine learning frameworks" 5
    """
    if not args.strip():
        return {"error": "Forneça um tópico de pesquisa. Exemplo: /auto_research artificial intelligence"}
    
    parts = args.strip().rsplit(maxsplit=1)
    
    # Verificar se último argumento é um número (quantidade de sites)
    topic = args.strip()
    num_sites = 3
    
    if len(parts) == 2 and parts[1].isdigit():
        topic = parts[0]
        num_sites = min(int(parts[1]), 10)  # Máximo 10 sites
    
    response = f"🔬 **Iniciando pesquisa completa sobre:** {topic}\n"
    response += f"📊 **Analisando {num_sites} sites principais...**\n\n"
    response += "⏳ *Isso pode levar alguns minutos...*\n\n"
    
    # Retornar resposta inicial imediatamente
    master = get_automation_master()
    
    try:
        result = master.auto_research_and_save(topic, num_sites)
        
        if "error" in result:
            return result
        
        response += f"✅ **Pesquisa concluída!**\n\n"
        response += f"📊 **Sites analisados:** {result['sites_analyzed']}\n"
        response += f"💾 **Relatório salvo:** {result['report_file']}\n\n"
        
        # Resumo dos sites analisados
        if "report" in result and "detailed_analysis" in result["report"]:
            response += "🌐 **Sites analisados:**\n"
            for i, site in enumerate(result["report"]["detailed_analysis"], 1):
                response += f"{i}. {site['title'][:60]}...\n"
                response += f"   🔗 {site['url']}\n"
        
        return {
            "success": True,
            "message": response,
            "data": result
        }
        
    except Exception as e:
        return {"error": f"Erro na pesquisa: {str(e)}"}

def handle_auto_type(args: str) -> Dict[str, Any]:
    """
    Digitar texto automaticamente
    Uso: /auto_type Hello World!
    """
    if not args:
        return {"error": "Forneça o texto a ser digitado. Exemplo: /auto_type Hello World!"}
    
    master = get_automation_master()
    result = master.type_text(args)
    
    if "error" in result:
        return result
    
    response = f"⌨️ **Texto digitado!**\n"
    response += f"📝 **Conteúdo:** {result['text_typed']}\n"
    response += f"🔢 **Caracteres:** {result['char_count']}"
    
    return {
        "success": True,
        "message": response,
        "data": result
    }

def handle_auto_keys(args: str) -> Dict[str, Any]:
    """
    Pressionar combinação de teclas
    Uso: /auto_keys ctrl c
    Uso: /auto_keys alt tab
    Uso: /auto_keys ctrl shift n
    """
    if not args.strip():
        return {"error": "Forneça as teclas. Exemplo: /auto_keys ctrl c"}
    
    keys = args.strip().split()
    if not keys:
        return {"error": "Nenhuma tecla fornecida"}
    
    master = get_automation_master()
    result = master.press_key_combination(*keys)
    
    if "error" in result:
        return result
    
    response = f"⌨️ **Combinação de teclas pressionada!**\n"
    response += f"🎹 **Teclas:** {result['keys_pressed']}"
    
    return {
        "success": True,
        "message": response,
        "data": result
    }

def handle_auto_folder(args: str) -> Dict[str, Any]:
    """
    Abrir pasta no Windows Explorer
    Uso: /auto_folder C:/meu_projeto_livre
    Uso: /auto_folder C:/Users/usuario/Documents
    """
    if not args.strip():
        # CORREÇÃO: Usar forward slashes para evitar unicode escape error
        return {"error": "Forneça o caminho da pasta. Exemplo: /auto_folder C:/meu_projeto_livre"}
    
    master = get_automation_master()
    result = master.open_folder(args.strip())
    
    if "error" in result:
        return result
    
    response = f"📁 **Pasta aberta!**\n"
    response += f"📂 **Caminho:** {result['folder_opened']}"
    
    return {
        "success": True,
        "message": response,
        "data": result
    }

def handle_auto_find_files(args: str) -> Dict[str, Any]:
    """
    Buscar arquivos em diretório
    Uso: /auto_find_files C:/meu_projeto_livre *.py
    Uso: /auto_find_files C:/Users/usuario/Documents *.txt
    """
    parts = args.strip().split(maxsplit=1)
    if len(parts) < 1:
        # CORREÇÃO: Usar forward slashes
        return {"error": "Forneça o caminho. Exemplo: /auto_find_files C:/meu_projeto_livre *.py"}
    
    search_path = parts[0]
    pattern = parts[1] if len(parts) > 1 else "*"
    
    master = get_automation_master()
    result = master.search_files(search_path, pattern)
    
    if "error" in result:
        return result
    
    response = f"🔍 **Busca de arquivos concluída!**\n"
    response += f"📂 **Pasta:** {result['search_path']}\n"
    response += f"🔎 **Padrão:** {result['pattern']}\n"
    response += f"📊 **Arquivos encontrados:** {result['files_found']}\n\n"
    
    if result.get("files"):
        response += "📋 **Primeiros arquivos:**\n"
        for file_info in result["files"][:10]:  # Mostrar primeiros 10
            response += f"📄 {file_info['name']} ({file_info['size']} bytes)\n"
            response += f"   📅 {file_info['modified'][:10]}\n"
    
    return {
        "success": True,
        "message": response,
        "data": result
    }

def handle_auto_status(args: str = None) -> Dict[str, Any]:
    """
    Status do sistema de automação
    Uso: /auto_status
    """
    try:
        master = get_automation_master()
        
        response = "🤖 **STATUS DO SISTEMA DE AUTOMAÇÃO**\n\n"
        
        # Verificar componentes
        response += "⚙️ **Componentes:**\n"
        
        # Selenium
        try:
            from selenium import webdriver
            selenium_status = "✅ Disponível"
        except ImportError:
            selenium_status = "❌ Não instalado"
        
        response += f"🌐 Selenium (Web): {selenium_status}\n"
        
        # PyAutoGUI
        try:
            import pyautogui
            pyautogui_status = "✅ Disponível"
        except ImportError:
            pyautogui_status = "❌ Não instalado"
        
        response += f"🖱️ PyAutoGUI (Desktop): {pyautogui_status}\n"
        
        # DuckDuckGo
        try:
            from duckduckgo_search import DDGS
            ddg_status = "✅ Disponível"
        except ImportError:
            ddg_status = "❌ Não instalado"
        
        response += f"🔍 DuckDuckGo (Busca): {ddg_status}\n\n"
        
        # Diretórios - CORREÇÃO: Usar Path para evitar unicode errors
        response += "📁 **Diretórios:**\n"
        free_path_str = str(master.free_path).replace(os.sep, '/')  # Normalizar separadores
        response += f"📂 Pasta livre: {free_path_str}\n"
        response += f"📸 Screenshots: {free_path_str}/screenshots\n"
        response += f"🔬 Pesquisas: {free_path_str}/research\n\n"
        
        # Browser status
        browser_status = "🌐 Browser: "
        if master.driver:
            browser_status += "✅ Ativo"
        else:
            browser_status += "💤 Inativo"
        response += browser_status + "\n\n"
        
        # Comandos disponíveis
        response += "🔧 **Comandos disponíveis:**\n"
        commands = [
            "/auto_search <query> - Buscar na internet",
            "/auto_browse <url> - Navegar para site",
            "/auto_click <selector> - Clicar em elemento",
            "/auto_screenshot [nome] - Capturar tela",
            "/auto_research <topic> [sites] - Pesquisa completa",
            "/auto_type <texto> - Digitar texto",
            "/auto_keys <key1> <key2> - Pressionar teclas",
            "/auto_folder <path> - Abrir pasta",
            "/auto_find_files <path> [pattern] - Buscar arquivos"
        ]
        
        for cmd in commands:
            response += f"   {cmd}\n"
        
        return {
            "success": True,
            "message": response,
            "selenium": selenium_status,
            "pyautogui": pyautogui_status, 
            "duckduckgo": ddg_status,
            "browser_active": master.driver is not None,
            "free_path": free_path_str
        }
        
    except Exception as e:
        return {"error": f"Erro ao verificar status: {str(e)}"}

# ============================================================================
# MAPA DE COMANDOS PARA INTEGRAÇÃO COM MAIN_AGENT.PY
# ============================================================================

AUTOMATION_COMMAND_MAP = {
    "auto_search": handle_auto_search,
    "auto_browse": handle_auto_browse,
    "auto_click": handle_auto_click,
    "auto_screenshot": handle_auto_screenshot,
    "auto_research": handle_auto_research,
    "auto_type": handle_auto_type,
    "auto_keys": handle_auto_keys,
    "auto_folder": handle_auto_folder,
    "auto_find_files": handle_auto_find_files,
    "auto_status": handle_auto_status
}

def handle_automation_command(command: str, args: str = "") -> Dict[str, Any]:
    """
    Handler unificado para todos os comandos de automação
    
    Args:
        command (str): Comando sem o prefixo / (ex: "auto_search")
        args (str): Argumentos do comando
    
    Returns:
        Dict[str, Any]: Resultado da execução
    """
    if command in AUTOMATION_COMMAND_MAP:
        handler = AUTOMATION_COMMAND_MAP[command]
        
        # Alguns comandos não precisam de argumentos
        if command in ["auto_screenshot", "auto_status"]:
            return handler(args) if args else handler()
        else:
            return handler(args)
    else:
        return {
            "error": f"Comando de automação desconhecido: {command}",
            "available_commands": list(AUTOMATION_COMMAND_MAP.keys())
        }

# ============================================================================
# FUNÇÃO DE INSTALAÇÃO AUTOMÁTICA (SE NECESSÁRIO)
# ============================================================================

def ensure_automation_dependencies():
    """Verificar e instalar dependências se necessário"""
    missing = []
    
    try:
        import selenium
    except ImportError:
        missing.append("selenium")
    
    try:
        import pyautogui
    except ImportError:
        missing.append("pyautogui")
    
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        missing.append("duckduckgo-search")
    
    if missing:
        return {
            "dependencies_missing": True,
            "missing_packages": missing,
            "install_command": f"pip install {' '.join(missing)}"
        }
    else:
        return {"dependencies_missing": False}