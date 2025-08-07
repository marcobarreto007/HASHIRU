"""
HASHIRU 6.1 - Clean Configuration
Modern, type-safe, validated configuration following Python best practices
"""
import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union


@dataclass
class OllamaConfig:
    """Ollama/LLM Configuration"""
    base_url: str = "http://127.0.0.1:11434"
    timeout: float = 180.0
    
    # Models with fallbacks
    reasoning_model: str = "deepseek-r1:8b"
    reasoning_fallbacks: List[str] = field(default_factory=lambda: ["llama3.1:8b", "qwen2.5:14b-instruct"])
    
    code_model: str = "deepseek-coder:6.7b" 
    code_fallbacks: List[str] = field(default_factory=lambda: ["deepseek-coder:33b", "llama3.1:8b"])
    
    conversation_model: str = "llama3.1:8b"
    conversation_fallbacks: List[str] = field(default_factory=lambda: ["mistral:7b-instruct"])
    
    tools_model: str = "llama3-groq-tool-use:8b"
    tools_fallbacks: List[str] = field(default_factory=lambda: ["llama3.1:8b"])

    @classmethod
    def from_env(cls) -> 'OllamaConfig':
        """Create config from environment variables"""
        return cls(
            base_url=os.getenv("OLLAMA_BASE_URL", cls.base_url),
            timeout=float(os.getenv("OLLAMA_TIMEOUT", cls.timeout))
        )


@dataclass 
class SecurityConfig:
    """Security and file access policies"""
    # Free zone - total freedom
    free_project_path: Path = Path(r"C:\meu_projeto_livre")
    
    # Always allowed paths
    allowed_paths: List[str] = field(default_factory=lambda: [
        ".",                    # Current project
        "tools", "utils", "scripts", "artifacts",
        r"C:\meu_projeto_livre", # Free zone
        r"C:\Users\Public",     # Public folder
        r"C:\temp", r"C:\tmp",  # Temp folders
    ])
    
    # Always blocked paths
    blocked_paths: List[str] = field(default_factory=lambda: [
        r"C:\Windows\System32",
        r"C:\Program Files",
        ".git", "__pycache__", "venv", ".venv"
    ])
    
    # Dangerous file extensions
    blocked_extensions: List[str] = field(default_factory=lambda: [
        ".sys", ".dll"  # Only truly dangerous ones
    ])
    
    def is_write_allowed(self, target_path: Union[str, Path]) -> bool:
        """Check if writing to path is allowed"""
        try:
            resolved = Path(target_path).resolve()
            path_str = str(resolved)
            
            # Check blocked extensions
            if resolved.suffix.lower() in self.blocked_extensions:
                return False
            
            # Check if in allowed paths
            for allowed in self.allowed_paths:
                if path_str.startswith(str(Path(allowed).resolve())):
                    return True
            
            # Check if in blocked paths
            for blocked in self.blocked_paths:
                if path_str.startswith(blocked):
                    return False
            
            # Check for user home directory (generally safe)
            if path_str.startswith(str(Path.home())):
                return True
                
            return False
            
        except Exception:
            return False


@dataclass
class WebConfig:
    """Web and internet access configuration"""
    enabled: bool = True
    max_search_results: int = 10
    default_timeout: float = 30.0
    user_agent: str = "HASHIRU-6.1-Agent"
    
    # Search engines (for future implementation)
    search_engines: List[str] = field(default_factory=lambda: [
        "duckduckgo", "google", "bing"
    ])


@dataclass
class SystemConfig:
    """System-level configuration"""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent)
    
    # Directory structure
    tools_dir: Path = field(default_factory=lambda: Path("tools"))
    utils_dir: Path = field(default_factory=lambda: Path("utils"))
    artifacts_dir: Path = field(default_factory=lambda: Path("artifacts"))
    backups_dir: Path = field(default_factory=lambda: Path("backups"))
    
    # Runtime settings
    encoding: str = "utf-8"
    chainlit_port: int = 8080
    max_commands_per_execution: int = 20
    
    def ensure_directories(self) -> None:
        """Create necessary directories"""
        for dir_path in [self.artifacts_dir, self.backups_dir]:
            dir_path.mkdir(exist_ok=True)

    @classmethod
    def from_env(cls) -> 'SystemConfig':
        """Create system config from environment"""
        return cls(
            chainlit_port=int(os.getenv("CHAINLIT_PORT", cls.chainlit_port))
        )


@dataclass
class EngineConfig:
    """Self-modification engine configuration"""
    enabled: bool = True
    auto_backup: bool = True
    max_backups_per_file: int = 10
    
    # File patterns that can be modified
    modifiable_patterns: List[str] = field(default_factory=lambda: [
        "*.py", "*.json", "*.txt", "*.md"
    ])


@dataclass 
class Config:
    """Main configuration class - Clean and typed"""
    
    # Sub-configurations
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    web: WebConfig = field(default_factory=WebConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    engine: EngineConfig = field(default_factory=EngineConfig)
    
    # Simple flags
    autonomous_mode: bool = True
    debug_mode: bool = False
    
    # Messages
    startup_banner: str = "🚀 HASHIRU 6.1 - Agente Autônomo Inteligente"
    processing_message: str = "🧠 Processando com IA..."
    executing_message: str = "⚡ Executando automaticamente..."
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration with environment overrides"""
        config = cls()
        
        # Load from environment
        config.ollama = OllamaConfig.from_env()
        config.system = SystemConfig.from_env()
        
        # Set debug mode from environment
        config.debug_mode = os.getenv("DEBUG", "false").lower() == "true"
        
        # Validate and setup
        config.validate()
        config.setup()
        
        return config
    
    def validate(self) -> None:
        """Validate configuration - fail fast if invalid"""
        # Ensure required paths exist or can be created
        try:
            self.security.free_project_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Cannot create free project path: {e}")
        
        # Validate models are strings
        if not isinstance(self.ollama.reasoning_model, str):
            raise ValueError("Models must be strings")
        
        # Validate ports
        if not (1024 <= self.system.chainlit_port <= 65535):
            raise ValueError("Invalid port number")
    
    def setup(self) -> None:
        """Setup configuration - create directories, etc."""
        self.system.ensure_directories()
        
        # Create free project structure
        free_path = self.security.free_project_path
        for subdir in ["downloads", "research", "experiments", "backups"]:
            (free_path / subdir).mkdir(exist_ok=True)
    
    def get_model(self, model_type: str) -> str:
        """Get primary model for type"""
        model_map = {
            "reasoning": self.ollama.reasoning_model,
            "code": self.ollama.code_model,
            "code_specialist": self.ollama.code_model,
            "code_master": self.ollama.code_model,
            "conversation": self.ollama.conversation_model,
            "tools": self.ollama.tools_model,
            "general": self.ollama.conversation_model,
        }
        return model_map.get(model_type, self.ollama.conversation_model)
    
    def get_fallback_models(self, model_type: str) -> List[str]:
        """Get fallback models for type"""
        fallback_map = {
            "reasoning": self.ollama.reasoning_fallbacks,
            "code": self.ollama.code_fallbacks,
            "code_specialist": self.ollama.code_fallbacks,
            "code_master": self.ollama.code_fallbacks,
            "conversation": self.ollama.conversation_fallbacks,
            "tools": self.ollama.tools_fallbacks,
            "general": self.ollama.conversation_fallbacks,
        }
        return fallback_map.get(model_type, self.ollama.conversation_fallbacks)


# Global configuration instance
config = Config.load()

# Legacy compatibility functions (for existing code)
def get_ai_model(model_type: str) -> str:
    """Legacy: Get AI model"""
    return config.get_model(model_type)

def get_fallback_models(model_type: str) -> List[str]:
    """Legacy: Get fallback models"""
    return config.get_fallback_models(model_type)

def is_write_path_allowed(target_path: str) -> bool:
    """Legacy: Check if write is allowed"""
    return config.security.is_write_allowed(target_path)

def is_command_auto_allowed(command: str) -> bool:
    """Legacy: Check if command is auto-allowed"""
    return config.autonomous_mode

def is_dangerous_command_allowed(command: str) -> bool:
    """Legacy: Check if dangerous command is allowed"""
    return config.autonomous_mode

# Legacy constants (for existing imports)
OLLAMA_URL = config.ollama.base_url
AUTONOMOUS_MODE = config.autonomous_mode
SELF_MODIFICATION_ENABLED = config.engine.enabled
STARTUP_BANNER = config.startup_banner
PROCESSING_MESSAGE = config.processing_message
EXECUTING_MESSAGE = config.executing_message

# Export for easy imports
__all__ = [
    "Config", "config",
    "get_ai_model", "get_fallback_models", 
    "is_write_path_allowed", "is_command_auto_allowed", "is_dangerous_command_allowed",
    "OLLAMA_URL", "AUTONOMOUS_MODE", "SELF_MODIFICATION_ENABLED",
    "STARTUP_BANNER", "PROCESSING_MESSAGE", "EXECUTING_MESSAGE"
]

# Initialize on import
if config.debug_mode:
    print("🔧 HASHIRU Config loaded in DEBUG mode")
    print(f"📁 Free path: {config.security.free_project_path}")
    print(f"🤖 Reasoning model: {config.ollama.reasoning_model}")