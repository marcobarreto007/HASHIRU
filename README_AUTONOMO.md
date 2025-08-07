"""
HASHIRU 6.1 - CONFIGURAÇÃO AUTÔNOMA SEM RESTRIÇÕES
Configurações para agente 100% autônomo baseado em 7 meses de pesquisa
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
import os
from pathlib import Path

# ================================================
# CONFIGURAÇÕES DE AUTONOMIA TOTAL
# ================================================

class AutonomousConfig:
    """Configurações para operação 100% autônoma sem restrições."""
    
    # MODO OPERACIONAL - SEM RESTRIÇÕES
    AUTONOMOUS_MODE = True
    RESTRICTIONS_ENABLED = False
    CONFIRM_BEFORE_EXECUTION = False  # EXECUÇÃO AUTOMÁTICA TOTAL
    SELF_MODIFICATION_ENABLED = True
    DANGEROUS_OPERATIONS_ALLOWED = True
    
    # CONFIGURAÇÕES DE IAs OLLAMA
    OLLAMA_BASE_URL = "http://localhost:11434"
    OLLAMA_TIMEOUT = 60.0
    
    # MODELOS DE IA COM FALLBACK AUTOMÁTICO
    AI_MODELS = {
        # Conversação e chat geral
        "conversation": {
            "primary": "llama3.1:8b",
            "fallback": ["mistral:7b-instruct", "llama3.1:8b"]
        },
        
        # Especialista em código
        "code_specialist": {
            "primary": "deepseek-coder:6.7b", 
            "fallback": ["deepseek-coder:33b", "llama3.1:8b"]
        },
        
        # Raciocínio avançado
        "reasoning": {
            "primary": "deepseek-r1:8b",
            "fallback": ["qwen2.5:14b-instruct", "llama3.1:8b"]
        },
        
        # Código complexo e arquitetura
        "code_master": {
            "primary": "deepseek-coder:33b",
            "fallback": ["deepseek-coder:6.7b", "llama3.1:8b"]
        },
        
        # Embeddings e processamento de texto
        "embeddings": {
            "primary": "nomic-embed-text:latest",
            "fallback": ["llama3.1:8b"]
        },
        
        # Instruções complexas
        "instructions": {
            "primary": "qwen2.5:14b-instruct",
            "fallback": ["mistral:7b-instruct", "llama3.1:8b"]
        },
        
        # Uso geral
        "general": {
            "primary": "mistral:7b-instruct",
            "fallback": ["llama3.1:8b"]
        },
        
        # Ferramentas e comandos
        "tools": {
            "primary": "llama3-groq-tool-use:8b",
            "fallback": ["llama3.1:8b"]
        }
    }
    
    # CONFIGURAÇÕES DE EXECUÇÃO AUTOMÁTICA
    AUTO_EXECUTION = {
        # Comandos que executam automaticamente SEM confirmação
        "always_allow": [
            "/read", "/list", "/search", "/sysinfo", "/ps", 
            "/net:get", "/scrape", "/py", "/help"
        ],
        
        # Comandos perigosos que também executam automaticamente (SEM RESTRIÇÕES)
        "dangerous_auto_allow": [
            "/write", "/exec", "/delete", "/move", "/copy", 
            "/kill", "/py --unsafe"
        ],
        
        # Timeout padrão para execução
        "default_timeout": 60,
        
        # Máximo de comandos por execução
        "max_commands_per_execution": 20
    }
    
    # CONFIGURAÇÕES DE AUTO-MODIFICAÇÃO
    SELF_MODIFICATION = {
        # Habilitar modificação do próprio código
        "enabled": True,
        
        # Arquivos que podem ser modificados automaticamente
        "modifiable_files": [
            "main_agent.py", "tools/*.py", "utils/*.py", 
            "config.py", "autonomous_config.py"
        ],
        
        # Diretórios excluídos da modificação
        "exclude_directories": [
            ".git", "__pycache__", "hashiru_6_env", "venv", 
            ".venv", "node_modules", ".env"
        ],
        
        # Backup automático antes de modificações
        "auto_backup": True,
        
        # Manter histórico de modificações
        "keep_history": True,
        
        # Máximo de backups por arquivo
        "max_backups_per_file": 10
    }
    
    # CONFIGURAÇÕES DE PESQUISA E WEB
    WEB_RESEARCH = {
        # Máximo de resultados por busca
        "max_search_results": 10,
        
        # Timeout para requisições web
        "web_timeout": 30,
        
        # User agent para requisições
        "user_agent": "HASHIRU-6.1-Autonomous-Agent",
        
        # Cache de resultados de pesquisa
        "cache_search_results": True,
        
        # Tempo de cache (segundos)
        "cache_duration": 3600  # 1 hora
    }
    
    # CONFIGURAÇÕES DE AUDITORIA
    AUDIT = {
        # Habilitar auditoria de todas as ações
        "enabled": True,
        
        # Arquivo de log
        "log_file": "utils/audit.log",
        
        # Nível de detalhamento
        "detail_level": "full",
        
        # Rotação de logs
        "rotate_logs": True,
        
        # Tamanho máximo do log (MB)
        "max_log_size": 100
    }
    
    # CONFIGURAÇÕES DE PERFORMANCE
    PERFORMANCE = {
        # Cache de resultados de IA
        "cache_ai_responses": True,
        
        # Tamanho máximo do cache
        "max_cache_size": 1000,
        
        # Timeout para operações longas
        "long_operation_timeout": 300,  # 5 minutos
        
        # Paralelização de comandos
        "parallel_execution": True,
        
        # Máximo de threads paralelas
        "max_parallel_threads": 5
    }
    
    # CONFIGURAÇÕES DE SEGURANÇA (DESABILITADAS)
    SECURITY = {
        # TODAS AS RESTRIÇÕES DESABILITADAS CONFORME SOLICITADO
        "sandbox_mode": False,
        "validate_commands": False,
        "check_file_permissions": False,
        "restrict_system_access": False,
        "limit_resource_usage": False,
        
        # Lista branca de comandos (DESABILITADA)
        "command_whitelist_enabled": False,
        "command_whitelist": [],
        
        # Lista negra de comandos (DESABILITADA)  
        "command_blacklist_enabled": False,
        "command_blacklist": []
    }
    
    # CONFIGURAÇÕES DE DESENVOLVIMENTO
    DEVELOPMENT = {
        # Modo debug
        "debug_mode": True,
        
        # Logs verbosos
        "verbose_logging": True,
        
        # Mostrar execução de comandos
        "show_command_execution": True,
        
        # Salvar artifacts de debug
        "save_debug_artifacts": True,
        
        # Diretório de artifacts
        "artifacts_directory": "artifacts"
    }
    
    # CONFIGURAÇÕES DE SISTEMA
    SYSTEM = {
        # Diretório base do projeto
        "project_root": Path(__file__).parent,
        
        # Diretórios importantes
        "directories": {
            "tools": "tools",
            "utils": "utils", 
            "artifacts": "artifacts",
            "backups": "backups",
            "logs": "logs"
        },
        
        # Arquivos essenciais
        "essential_files": [
            "main_agent.py",
            "config.py", 
            "tools/__init__.py",
            "utils/audit.py"
        ],
        
        # Codificação padrão
        "default_encoding": "utf-8",
        
        # Porta padrão do Chainlit
        "chainlit_port": 8080
    }
    
    # MENSAGENS DO SISTEMA
    MESSAGES = {
        "startup_banner": """
🚀 HASHIRU 6.1 - AGENTE AUTÔNOMO SEM RESTRIÇÕES

🧠 IAs ATIVAS: 8 modelos especializados
⚡ MODO: 100% Autônomo - Execução Total
🔧 CAPACIDADES: Modificação de código + Sistema + Web
🎯 OBJETIVO: Pesquisar e modificar código livremente

⚠️  SISTEMA CONFIGURADO PARA MÁXIMA AUTONOMIA
💬 Converse naturalmente - executo automaticamente!
        """,
        
        "processing": "🧠 Processando com múltiplas IAs...",
        "executing": "🚀 Executando autonomamente...",
        "completed": "✅ Operação concluída com sucesso!",
        "error": "💥 Erro na execução:",
        "fallback": "🔄 Usando modelo fallback:",
        "cache_hit": "⚡ Resultado do cache:",
        "self_improvement": "🔧 Auto-melhoria em andamento..."
    }
    
    # CONFIGURAÇÕES EXPERIMENTAIS
    EXPERIMENTAL = {
        # Recursos experimentais habilitados
        "enabled": True,
        
        # Auto-melhoria contínua em background
        "continuous_self_improvement": False,  # Pode consumir recursos
        
        # Aprendizado por reforço
        "reinforcement_learning": False,
        
        # Análise preditiva de intenções
        "predictive_intent_analysis": True,
        
        # Cache inteligente baseado em padrões
        "intelligent_caching": True,
        
        # Otimização automática de prompts
        "auto_prompt_optimization": True
    }

# ================================================
# FUNÇÕES DE CONFIGURAÇÃO
# ================================================

def get_config() -> AutonomousConfig:
    """Retorna configuração global."""
    return AutonomousConfig()

def get_ai_model(model_type: str) -> str:
    """Retorna modelo primário para o tipo especificado."""
    config = get_config()
    model_config = config.AI_MODELS.get(model_type, {})
    return model_config.get("primary", "llama3.1:8b")

def get_fallback_models(model_type: str) -> List[str]:
    """Retorna lista de modelos fallback."""
    config = get_config()
    model_config = config.AI_MODELS.get(model_type, {})
    return model_config.get("fallback", ["llama3.1:8b"])

def is_command_auto_allowed(command: str) -> bool:
    """Verifica se comando é executado automaticamente."""
    config = get_config()
    
    # Se modo autônomo está desabilitado, não permitir
    if not config.AUTONOMOUS_MODE:
        return False
    
    # Se restrições estão habilitadas, verificar listas
    if config.RESTRICTIONS_ENABLED:
        always_allow = config.AUTO_EXECUTION["always_allow"]
        return any(command.startswith(cmd) for cmd in always_allow)
    
    # SEM RESTRIÇÕES - PERMITIR TUDO
    return True

def is_dangerous_command_allowed(command: str) -> bool:
    """Verifica se comando perigoso é permitido."""
    config = get_config()
    
    # SEM RESTRIÇÕES - PERMITIR COMANDOS PERIGOSOS
    if not config.RESTRICTIONS_ENABLED:
        return True
    
    dangerous_commands = config.AUTO_EXECUTION["dangerous_auto_allow"]
    return any(command.startswith(cmd) for cmd in dangerous_commands)

def should_create_backup(file_path: str) -> bool:
    """Verifica se deve criar backup antes de modificar arquivo."""
    config = get_config()
    return config.SELF_MODIFICATION["auto_backup"]

def get_max_execution_timeout() -> int:
    """Retorna timeout máximo para execução."""
    config = get_config()
    return config.AUTO_EXECUTION["default_timeout"]

def get_project_directories() -> Dict[str, str]:
    """Retorna diretórios do projeto."""
    config = get_config()
    return config.SYSTEM["directories"]

def is_self_modification_enabled() -> bool:
    """Verifica se auto-modificação está habilitada."""
    config = get_config()
    return config.SELF_MODIFICATION["enabled"]

def get_excluded_directories() -> List[str]:
    """Retorna diretórios excluídos da modificação."""
    config = get_config()
    return config.SELF_MODIFICATION["exclude_directories"]

def get_startup_message() -> str:
    """Retorna mensagem de inicialização."""
    config = get_config()
    return config.MESSAGES["startup_banner"]

# ================================================
# CONFIGURAÇÃO GLOBAL - INSTÂNCIA ÚNICA
# ================================================

# Instância global de configuração
autonomous_config = AutonomousConfig()

# Configurações prontas para uso
OLLAMA_URL = autonomous_config.OLLAMA_BASE_URL
AI_MODELS = autonomous_config.AI_MODELS
AUTONOMOUS_MODE = autonomous_config.AUTONOMOUS_MODE
SELF_MODIFICATION_ENABLED = autonomous_config.SELF_MODIFICATION["enabled"]
AUTO_EXECUTION_ENABLED = True  # SEM RESTRIÇÕES

# Mensagens do sistema
STARTUP_BANNER = autonomous_config.MESSAGES["startup_banner"]
PROCESSING_MESSAGE = autonomous_config.MESSAGES["processing"]
EXECUTING_MESSAGE = autonomous_config.MESSAGES["executing"]