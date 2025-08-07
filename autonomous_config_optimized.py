# -*- coding: utf-8 -*-
"""
HASHIRU 6.1 - OPTIMIZED CONFIGURATION 2025
Hardware-Specific AI Model Configuration based on 2025 Research

Optimizations:
- RTX 3060 (12GB) + RTX 2060 (6GB) specific model selection
- Performance vs Quality balanced configurations
- Type-safe dataclasses with runtime validation
- Environment variable override support
- Immutable configuration with validation
- Memory-efficient model allocation

Research Sources:
- GPU memory optimization studies (NVIDIA 2025)
- Dual GPU LLM inference benchmarks
- Python dataclass best practices
- Production-ready configuration management
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Union, Any, Tuple
from enum import Enum

# Configure logging
logger = logging.getLogger("hashiru.config")

# ============================================================================
# ENUMS FOR TYPE SAFETY
# ============================================================================

class ModelSize(Enum):
    """Model size categories optimized for dual GPU setup"""
    SMALL_3B = "3B"      # RTX 2060 compatible
    MEDIUM_7B = "7B"     # RTX 3060 optimized
    LARGE_8B = "8B"      # RTX 3060 + quantization
    XLARGE_14B = "14B"   # RTX 3060 + some RTX 2060
    PREMIUM_33B = "33B"  # Requires both GPUs (slow)

class Precision(Enum):
    """Precision formats for memory optimization"""
    FP16 = "fp16"        # Standard precision
    INT8 = "int8"        # 2x memory reduction
    INT4 = "int4"        # 4x memory reduction
    FP8 = "fp8"          # Emerging standard

class ModelType(Enum):
    """Model usage types for specialized selection"""
    REASONING = "reasoning"
    CODE = "code"
    CONVERSATION = "conversation"
    TOOLS = "tools"
    RESEARCH = "research"
    GENERAL = "general"

# ============================================================================
# HARDWARE-OPTIMIZED MODEL CONFIGURATIONS
# ============================================================================

@dataclass(frozen=True)
class ModelConfig:
    """Single model configuration with hardware specifications"""
    name: str
    size: ModelSize
    vram_requirement_gb: float
    recommended_precision: Precision
    performance_tier: int  # 1=best, 5=acceptable
    tokens_per_second_estimate: int
    description: str
    
    def is_compatible_with_vram(self, available_vram_gb: float) -> bool:
        """Check if model fits in available VRAM"""
        return self.vram_requirement_gb <= available_vram_gb

@dataclass(frozen=True)
class HardwareProfile:
    """Hardware specification for model selection"""
    gpu_primary: str
    gpu_secondary: Optional[str]
    vram_primary_gb: float
    vram_secondary_gb: float
    total_vram_gb: float
    
    @property
    def is_dual_gpu(self) -> bool:
        return self.gpu_secondary is not None

# ============================================================================
# OPTIMIZED MODEL REGISTRY (2025 RESEARCH-BASED)
# ============================================================================

class OptimizedModelRegistry:
    """
    Hardware-optimized model registry based on 2025 performance research
    Specifically optimized for RTX 3060 (12GB) + RTX 2060 (6GB) setup
    """
    
    # Hardware profile for the user's setup
    DUAL_RTX_PROFILE = HardwareProfile(
        gpu_primary="RTX 3060",
        gpu_secondary="RTX 2060", 
        vram_primary_gb=12.0,
        vram_secondary_gb=6.0,
        total_vram_gb=18.0
    )
    
    # Optimized model configurations based on research
    MODELS = {
        # REASONING MODELS (Best for analysis, logic, planning)
        "reasoning_premium": ModelConfig(
            name="qwen2.5:14b-instruct",
            size=ModelSize.XLARGE_14B,
            vram_requirement_gb=9.0,  # Fits perfectly in RTX 3060
            recommended_precision=Precision.FP16,
            performance_tier=1,  # Best reasoning quality
            tokens_per_second_estimate=25,
            description="Premium reasoning model optimized for RTX 3060"
        ),
        "reasoning_balanced": ModelConfig(
            name="deepseek-r1:8b", 
            size=ModelSize.LARGE_8B,
            vram_requirement_gb=5.2,
            recommended_precision=Precision.FP16,
            performance_tier=2,
            tokens_per_second_estimate=35,
            description="Balanced reasoning with good speed"
        ),
        "reasoning_fallback": ModelConfig(
            name="llama3.1:8b",
            size=ModelSize.LARGE_8B, 
            vram_requirement_gb=4.9,
            recommended_precision=Precision.FP16,
            performance_tier=3,
            tokens_per_second_estimate=45,
            description="Fast reasoning fallback"
        ),
        
        # CODE MODELS (Optimized for programming)
        "code_optimal": ModelConfig(
            name="deepseek-coder:6.7b",
            size=ModelSize.MEDIUM_7B,
            vram_requirement_gb=3.8,  # Very efficient for RTX 3060
            recommended_precision=Precision.FP16,
            performance_tier=1,  # Best code quality for hardware
            tokens_per_second_estimate=50,
            description="Optimal code model for RTX 3060 - best speed/quality"
        ),
        "code_premium": ModelConfig(
            name="deepseek-coder:33b",
            size=ModelSize.PREMIUM_33B,
            vram_requirement_gb=18.0,  # Requires both GPUs
            recommended_precision=Precision.INT4,  # Quantized to fit
            performance_tier=5,  # Slow but highest quality
            tokens_per_second_estimate=8,
            description="Premium code model (slow on this hardware)"
        ),
        
        # CONVERSATION MODELS (Optimized for chat)
        "conversation_fast": ModelConfig(
            name="llama3.1:8b",
            size=ModelSize.LARGE_8B,
            vram_requirement_gb=4.9,
            recommended_precision=Precision.FP16,
            performance_tier=1,  # Best for conversation speed
            tokens_per_second_estimate=70,
            description="Fast conversation model - 70+ tokens/s"
        ),
        "conversation_premium": ModelConfig(
            name="qwen2.5:14b-instruct", 
            size=ModelSize.XLARGE_14B,
            vram_requirement_gb=9.0,
            recommended_precision=Precision.FP16,
            performance_tier=2,  # Higher quality, slower
            tokens_per_second_estimate=25,
            description="Premium conversation quality"
        ),
        
        # TOOLS MODELS (Specialized for automation)
        "tools_specialized": ModelConfig(
            name="llama3-groq-tool-use:8b",
            size=ModelSize.LARGE_8B,
            vram_requirement_gb=4.7,
            recommended_precision=Precision.FP16,
            performance_tier=1,  # Best for tool usage
            tokens_per_second_estimate=40,
            description="Specialized for automation and tools"
        ),
        
        # RESEARCH MODELS (Multi-source analysis)
        "research_balanced": ModelConfig(
            name="qwen2.5:14b-instruct",
            size=ModelSize.XLARGE_14B,
            vram_requirement_gb=9.0,
            recommended_precision=Precision.FP16,
            performance_tier=1,
            tokens_per_second_estimate=25,
            description="Excellent for research and analysis"
        ),
        
        # LIGHTWEIGHT MODELS (RTX 2060 compatible)
        "lightweight_3b": ModelConfig(
            name="llama3.2:3b",
            size=ModelSize.SMALL_3B,
            vram_requirement_gb=2.5,
            recommended_precision=Precision.FP16,
            performance_tier=4,  # Lower quality but very fast
            tokens_per_second_estimate=90,
            description="Ultra-fast 3B model for RTX 2060"
        )
    }
    
    @classmethod
    def get_optimal_model(cls, model_type: ModelType, hardware: HardwareProfile) -> str:
        """Get optimal model name for given type and hardware"""
        
        # Hardware-optimized mapping based on 2025 research
        optimal_mapping = {
            ModelType.REASONING: "reasoning_premium",   # qwen2.5:14b (9GB)
            ModelType.CODE: "code_optimal",             # deepseek-coder:6.7b (3.8GB)  
            ModelType.CONVERSATION: "conversation_fast", # llama3.1:8b (4.9GB)
            ModelType.TOOLS: "tools_specialized",       # llama3-groq-tool-use:8b (4.7GB)
            ModelType.RESEARCH: "research_balanced",     # qwen2.5:14b (9GB)
            ModelType.GENERAL: "conversation_fast"       # llama3.1:8b (4.9GB)
        }
        
        model_key = optimal_mapping.get(model_type, "conversation_fast")
        model_config = cls.MODELS[model_key]
        
        # Fallback to smaller model if doesn't fit in primary GPU
        if not model_config.is_compatible_with_vram(hardware.vram_primary_gb):
            fallback_mapping = {
                ModelType.REASONING: "reasoning_fallback",   # llama3.1:8b
                ModelType.CODE: "code_optimal",              # Already optimal
                ModelType.CONVERSATION: "lightweight_3b",    # llama3.2:3b
                ModelType.TOOLS: "conversation_fast",        # llama3.1:8b
                ModelType.RESEARCH: "reasoning_fallback",    # llama3.1:8b
                ModelType.GENERAL: "lightweight_3b"          # llama3.2:3b
            }
            model_key = fallback_mapping.get(model_type, "lightweight_3b")
            model_config = cls.MODELS[model_key]
        
        return model_config.name
    
    @classmethod
    def get_fallback_models(cls, model_type: ModelType) -> List[str]:
        """Get ordered list of fallback models for type"""
        
        fallback_chains = {
            ModelType.REASONING: [
                "reasoning_premium",     # qwen2.5:14b
                "reasoning_balanced",    # deepseek-r1:8b  
                "reasoning_fallback",    # llama3.1:8b
                "lightweight_3b"        # llama3.2:3b
            ],
            ModelType.CODE: [
                "code_optimal",          # deepseek-coder:6.7b
                "reasoning_fallback",    # llama3.1:8b (general purpose)
                "lightweight_3b"        # llama3.2:3b
            ],
            ModelType.CONVERSATION: [
                "conversation_fast",     # llama3.1:8b
                "conversation_premium",  # qwen2.5:14b
                "lightweight_3b"        # llama3.2:3b  
            ],
            ModelType.TOOLS: [
                "tools_specialized",     # llama3-groq-tool-use:8b
                "conversation_fast",     # llama3.1:8b
                "lightweight_3b"        # llama3.2:3b
            ],
            ModelType.RESEARCH: [
                "research_balanced",     # qwen2.5:14b
                "reasoning_fallback",    # llama3.1:8b
                "lightweight_3b"        # llama3.2:3b
            ]
        }
        
        fallback_keys = fallback_chains.get(model_type, ["conversation_fast", "lightweight_3b"])
        return [cls.MODELS[key].name for key in fallback_keys]

# ============================================================================
# CONFIGURATION DATACLASSES
# ============================================================================

@dataclass(frozen=True)
class OllamaConfig:
    """
    Ollama/LLM Configuration optimized for dual GPU setup
    Based on 2025 performance research and hardware capabilities
    """
    base_url: str = "http://127.0.0.1:11434"
    timeout: float = 180.0
    
    # Hardware profile
    hardware: HardwareProfile = field(default_factory=lambda: OptimizedModelRegistry.DUAL_RTX_PROFILE)
    
    # Optimized model assignments (hardware-specific)
    reasoning_model: str = field(
        default_factory=lambda: OptimizedModelRegistry.get_optimal_model(
            ModelType.REASONING, OptimizedModelRegistry.DUAL_RTX_PROFILE
        )
    )
    code_model: str = field(
        default_factory=lambda: OptimizedModelRegistry.get_optimal_model(
            ModelType.CODE, OptimizedModelRegistry.DUAL_RTX_PROFILE  
        )
    )
    conversation_model: str = field(
        default_factory=lambda: OptimizedModelRegistry.get_optimal_model(
            ModelType.CONVERSATION, OptimizedModelRegistry.DUAL_RTX_PROFILE
        )
    )
    tools_model: str = field(
        default_factory=lambda: OptimizedModelRegistry.get_optimal_model(
            ModelType.TOOLS, OptimizedModelRegistry.DUAL_RTX_PROFILE
        )
    )
    research_model: str = field(
        default_factory=lambda: OptimizedModelRegistry.get_optimal_model(
            ModelType.RESEARCH, OptimizedModelRegistry.DUAL_RTX_PROFILE
        )
    )
    
    # Fallback chains (hardware-optimized)
    reasoning_fallbacks: List[str] = field(
        default_factory=lambda: OptimizedModelRegistry.get_fallback_models(ModelType.REASONING)
    )
    code_fallbacks: List[str] = field(
        default_factory=lambda: OptimizedModelRegistry.get_fallback_models(ModelType.CODE)
    )
    conversation_fallbacks: List[str] = field(
        default_factory=lambda: OptimizedModelRegistry.get_fallback_models(ModelType.CONVERSATION)
    )
    tools_fallbacks: List[str] = field(
        default_factory=lambda: OptimizedModelRegistry.get_fallback_models(ModelType.TOOLS)
    )
    research_fallbacks: List[str] = field(
        default_factory=lambda: OptimizedModelRegistry.get_fallback_models(ModelType.RESEARCH)
    )
    
    def __post_init__(self):
        """Runtime validation of configuration"""
        if not self.base_url.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid Ollama URL: {self.base_url}")
        
        if self.timeout <= 0:
            raise ValueError(f"Timeout must be positive: {self.timeout}")
        
        # Log optimized configuration
        logger.info(f"🎯 Ollama Config Optimized for {self.hardware.gpu_primary} + {self.hardware.gpu_secondary}")
        logger.info(f"💻 Reasoning: {self.reasoning_model}")
        logger.info(f"🔧 Code: {self.code_model}")  
        logger.info(f"💬 Conversation: {self.conversation_model}")
        logger.info(f"🛠️ Tools: {self.tools_model}")
        logger.info(f"🔬 Research: {self.research_model}")
    
    @classmethod
    def from_env(cls) -> 'OllamaConfig':
        """Create config from environment variables with overrides"""
        base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        timeout = float(os.getenv("OLLAMA_TIMEOUT", "180.0"))
        
        # Environment overrides for specific models
        reasoning_override = os.getenv("HASHIRU_REASONING_MODEL")
        code_override = os.getenv("HASHIRU_CODE_MODEL")
        conversation_override = os.getenv("HASHIRU_CONVERSATION_MODEL")
        tools_override = os.getenv("HASHIRU_TOOLS_MODEL")
        
        config = cls(base_url=base_url, timeout=timeout)
        
        # Apply environment overrides if provided
        if reasoning_override:
            object.__setattr__(config, 'reasoning_model', reasoning_override)
        if code_override:
            object.__setattr__(config, 'code_model', code_override)
        if conversation_override:
            object.__setattr__(config, 'conversation_model', conversation_override)
        if tools_override:
            object.__setattr__(config, 'tools_model', tools_override)
            
        return config

@dataclass(frozen=True)
class SecurityConfig:
    """Enhanced security configuration with type safety"""
    
    # Free development zone
    free_project_path: Path = field(default_factory=lambda: Path("C:/hashiru_workspace"))
    
    # Allowed paths (immutable)
    allowed_paths: Tuple[str, ...] = (
        ".",                           # Current project
        "tools", "utils", "scripts", "artifacts", "research", "screenshots", "logs",
        "C:/hashiru_workspace",        # Free development zone
        "C:/Users/Public",             # Public folder
        "C:/temp", "C:/tmp",           # Temp folders
    )
    
    # Blocked paths (security-critical)
    blocked_paths: Tuple[str, ...] = (
        "C:/Windows/System32",
        "C:/Program Files", 
        "C:/Program Files (x86)",
        ".git", "__pycache__", "venv", ".venv", "node_modules"
    )
    
    # Dangerous extensions
    blocked_extensions: Tuple[str, ...] = (
        ".exe", ".dll", ".sys", ".bat", ".cmd", ".scr", ".pif"
    )
    
    def __post_init__(self):
        """Validate and setup security configuration"""
        try:
            self.free_project_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"🔒 Security: Free workspace at {self.free_project_path}")
        except Exception as e:
            logger.warning(f"⚠️ Could not create free workspace: {e}")
    
    def is_write_allowed(self, target_path: Union[str, Path]) -> bool:
        """Enhanced path validation with detailed logging"""
        try:
            resolved = Path(target_path).resolve()
            path_str = str(resolved).replace("\\", "/")  # Normalize separators
            
            # Check blocked extensions
            if resolved.suffix.lower() in self.blocked_extensions:
                logger.warning(f"🚫 Blocked extension: {resolved.suffix}")
                return False
            
            # Check blocked paths (case-insensitive)
            for blocked in self.blocked_paths:
                if path_str.lower().startswith(blocked.lower()):
                    logger.warning(f"🚫 Blocked path: {blocked}")
                    return False
            
            # Check allowed paths
            for allowed in self.allowed_paths:
                allowed_resolved = str(Path(allowed).resolve()).replace("\\", "/")
                if path_str.startswith(allowed_resolved):
                    logger.debug(f"✅ Allowed path: {allowed}")
                    return True
            
            # Check user home directory
            home_path = str(Path.home()).replace("\\", "/")
            if path_str.startswith(home_path):
                logger.debug("✅ User home directory access")
                return True
            
            logger.warning(f"🚫 Path not in allowed list: {path_str}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Path validation error: {e}")
            return False

@dataclass(frozen=True)
class PerformanceConfig:
    """Performance optimization settings based on 2025 research"""
    
    # Memory management
    enable_gpu_memory_optimization: bool = True
    max_concurrent_requests: int = 4  # Optimized for dual GPU
    enable_quantization: bool = True
    preferred_precision: Precision = Precision.FP16
    
    # Inference optimization
    enable_flash_attention: bool = True  # 2025 standard
    enable_kv_cache_optimization: bool = True
    batch_size_optimization: bool = True
    
    # Hardware-specific optimizations
    enable_tensor_parallelism: bool = True  # For dual GPU
    enable_pipeline_parallelism: bool = False  # Not needed for this setup
    
    def __post_init__(self):
        """Log performance configuration"""
        logger.info(f"⚡ Performance: GPU Memory Optimization: {self.enable_gpu_memory_optimization}")
        logger.info(f"⚡ Performance: Quantization: {self.enable_quantization}")
        logger.info(f"⚡ Performance: Flash Attention: {self.enable_flash_attention}")
        logger.info(f"⚡ Performance: Tensor Parallelism: {self.enable_tensor_parallelism}")

@dataclass(frozen=True)
class SystemConfig:
    """System-level configuration with validation"""
    
    project_root: Path = field(default_factory=lambda: Path(__file__).parent)
    
    # Directory structure (immutable)
    tools_dir: Path = field(default_factory=lambda: Path("tools"))
    utils_dir: Path = field(default_factory=lambda: Path("utils"))
    artifacts_dir: Path = field(default_factory=lambda: Path("artifacts"))
    backups_dir: Path = field(default_factory=lambda: Path("backups"))
    research_dir: Path = field(default_factory=lambda: Path("research"))
    screenshots_dir: Path = field(default_factory=lambda: Path("screenshots"))
    logs_dir: Path = field(default_factory=lambda: Path("logs"))
    
    # Runtime settings
    encoding: str = "utf-8"
    chainlit_port: int = 8080
    max_commands_per_execution: int = 20
    debug_mode: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    def __post_init__(self):
        """Setup and validate directories"""
        directories = [
            self.artifacts_dir, self.backups_dir, self.research_dir,
            self.screenshots_dir, self.logs_dir
        ]
        
        for directory in directories:
            try:
                directory.mkdir(exist_ok=True)
                logger.debug(f"📁 Directory ready: {directory}")
            except Exception as e:
                logger.warning(f"⚠️ Could not create {directory}: {e}")
        
        logger.info(f"🔧 System: Project root: {self.project_root}")
        logger.info(f"🔧 System: Debug mode: {self.debug_mode}")

@dataclass(frozen=True)
class Config:
    """
    Main configuration class - Hardware-optimized for RTX 3060 + RTX 2060
    Based on 2025 research and best practices
    """
    
    # Sub-configurations (immutable)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    system: SystemConfig = field(default_factory=SystemConfig)
    
    # Feature flags
    autonomous_mode: bool = True
    self_modification_enabled: bool = True
    
    # UI Messages (with proper encoding)
    startup_banner: str = "🚀 HASHIRU 6.1 - Agente Autônomo Inteligente"
    processing_message: str = "🧠 Processando com IA..."
    executing_message: str = "⚡ Executando automaticamente..."
    
    # Version and metadata
    version: str = "6.1.2025"
    build_date: str = field(default_factory=lambda: "2025-08-04")
    
    def __post_init__(self):
        """Post-initialization validation and setup"""
        
        # Validate port
        if not (1024 <= self.system.chainlit_port <= 65535):
            raise ValueError(f"Invalid port: {self.system.chainlit_port}")
        
        # Log configuration summary
        logger.info(f"🚀 HASHIRU {self.version} Configuration Loaded")
        logger.info(f"📊 Hardware: {self.ollama.hardware.gpu_primary} + {self.ollama.hardware.gpu_secondary}")
        logger.info(f"💾 Total VRAM: {self.ollama.hardware.total_vram_gb}GB")
        logger.info(f"🔧 Autonomous Mode: {self.autonomous_mode}")
        logger.info(f"🔄 Self-Modification: {self.self_modification_enabled}")
        
        # Log model assignments
        logger.info("🤖 Model Assignments:")
        logger.info(f"  🧠 Reasoning: {self.ollama.reasoning_model}")
        logger.info(f"  💻 Code: {self.ollama.code_model}")
        logger.info(f"  💬 Conversation: {self.ollama.conversation_model}")
        logger.info(f"  🛠️ Tools: {self.ollama.tools_model}")
        logger.info(f"  🔬 Research: {self.ollama.research_model}")
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration with environment overrides and validation"""
        try:
            # Load Ollama config with environment overrides
            ollama_config = OllamaConfig.from_env()
            
            # Override other settings from environment
            autonomous_mode = os.getenv("HASHIRU_AUTONOMOUS", "true").lower() == "true"
            self_modification = os.getenv("HASHIRU_SELF_MOD", "true").lower() == "true"
            
            # Create configuration
            config = cls(
                ollama=ollama_config,
                autonomous_mode=autonomous_mode,
                self_modification_enabled=self_modification
            )
            
            logger.info("✅ Configuration loaded successfully")
            return config
            
        except Exception as e:
            logger.error(f"❌ Configuration loading failed: {e}")
            raise
    
    def get_model(self, model_type: str) -> str:
        """Get primary model for type with improved mapping"""
        
        # Enhanced model type mapping
        model_map = {
            "reasoning": self.ollama.reasoning_model,
            "code": self.ollama.code_model,
            "code_specialist": self.ollama.code_model,
            "code_master": self.ollama.code_model,
            "programming": self.ollama.code_model,
            "conversation": self.ollama.conversation_model,
            "chat": self.ollama.conversation_model,
            "tools": self.ollama.tools_model,
            "automation": self.ollama.tools_model,
            "research": self.ollama.research_model,
            "analysis": self.ollama.research_model,
            "general": self.ollama.conversation_model,
            "default": self.ollama.conversation_model
        }
        
        model = model_map.get(model_type.lower(), self.ollama.conversation_model)
        logger.debug(f"🎯 Model selection: {model_type} -> {model}")
        return model
    
    def get_fallback_models(self, model_type: str) -> List[str]:
        """Get fallback models for type with enhanced mapping"""
        
        fallback_map = {
            "reasoning": self.ollama.reasoning_fallbacks,
            "code": self.ollama.code_fallbacks,
            "code_specialist": self.ollama.code_fallbacks,
            "programming": self.ollama.code_fallbacks,
            "conversation": self.ollama.conversation_fallbacks,
            "chat": self.ollama.conversation_fallbacks,
            "tools": self.ollama.tools_fallbacks,
            "automation": self.ollama.tools_fallbacks,
            "research": self.ollama.research_fallbacks,
            "analysis": self.ollama.research_fallbacks,
            "general": self.ollama.conversation_fallbacks,
        }
        
        fallbacks = fallback_map.get(model_type.lower(), self.ollama.conversation_fallbacks)
        logger.debug(f"🔄 Fallback chain: {model_type} -> {fallbacks}")
        return fallbacks

# ============================================================================
# GLOBAL CONFIGURATION INSTANCE
# ============================================================================

# Initialize configuration with error handling
try:
    config = Config.load()
    logger.info("🎉 HASHIRU Configuration initialized successfully")
except Exception as e:
    logger.error(f"💥 Configuration initialization failed: {e}")
    # Fallback to default configuration
    config = Config()
    logger.warning("⚠️ Using default configuration as fallback")

# ============================================================================
# LEGACY COMPATIBILITY FUNCTIONS
# ============================================================================

def get_ai_model(model_type: str) -> str:
    """Legacy: Get AI model with enhanced logging"""
    model = config.get_model(model_type)
    logger.debug(f"🔍 Legacy get_ai_model: {model_type} -> {model}")
    return model

def get_fallback_models(model_type: str) -> List[str]:
    """Legacy: Get fallback models"""
    return config.get_fallback_models(model_type)

def is_write_path_allowed(target_path: str) -> bool:
    """Legacy: Check if write is allowed"""
    return config.security.is_write_allowed(target_path)

def is_command_auto_allowed(command: str) -> bool:
    """Legacy: Check if command is auto-allowed"""
    allowed = config.autonomous_mode
    logger.debug(f"🤖 Auto command check: {command} -> {allowed}")
    return allowed

def is_dangerous_command_allowed(command: str) -> bool:
    """Legacy: Check if dangerous command is allowed"""
    allowed = config.autonomous_mode
    logger.debug(f"⚠️ Dangerous command check: {command} -> {allowed}")
    return allowed

# ============================================================================
# LEGACY CONSTANTS (for backward compatibility)
# ============================================================================

OLLAMA_URL = config.ollama.base_url
AUTONOMOUS_MODE = config.autonomous_mode
SELF_MODIFICATION_ENABLED = config.self_modification_enabled
STARTUP_BANNER = config.startup_banner
PROCESSING_MESSAGE = config.processing_message
EXECUTING_MESSAGE = config.executing_message

# Hardware information (new)
HARDWARE_PROFILE = config.ollama.hardware
PRIMARY_GPU = config.ollama.hardware.gpu_primary
SECONDARY_GPU = config.ollama.hardware.gpu_secondary
TOTAL_VRAM_GB = config.ollama.hardware.total_vram_gb

# Model information (new)
CURRENT_MODELS = {
    "reasoning": config.ollama.reasoning_model,
    "code": config.ollama.code_model,
    "conversation": config.ollama.conversation_model,
    "tools": config.ollama.tools_model,
    "research": config.ollama.research_model
}

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Main configuration
    "Config", "config",
    
    # Model registry and optimization
    "OptimizedModelRegistry", "ModelConfig", "HardwareProfile",
    "ModelSize", "Precision", "ModelType",
    
    # Configuration classes
    "OllamaConfig", "SecurityConfig", "PerformanceConfig", "SystemConfig",
    
    # Legacy functions
    "get_ai_model", "get_fallback_models",
    "is_write_path_allowed", "is_command_auto_allowed", "is_dangerous_command_allowed",
    
    # Legacy constants
    "OLLAMA_URL", "AUTONOMOUS_MODE", "SELF_MODIFICATION_ENABLED",
    "STARTUP_BANNER", "PROCESSING_MESSAGE", "EXECUTING_MESSAGE",
    
    # Hardware constants (new)
    "HARDWARE_PROFILE", "PRIMARY_GPU", "SECONDARY_GPU", "TOTAL_VRAM_GB",
    "CURRENT_MODELS"
]

# ============================================================================
# INITIALIZATION LOGGING
# ============================================================================

if config.system.debug_mode:
    logger.info("🔧 HASHIRU Config loaded in DEBUG mode")
    logger.info(f"📁 Free workspace: {config.security.free_project_path}")
    logger.info(f"🎯 Optimized for: {PRIMARY_GPU} ({config.ollama.hardware.vram_primary_gb}GB) + {SECONDARY_GPU} ({config.ollama.hardware.vram_secondary_gb}GB)")
    logger.info(f"🤖 Active models: {CURRENT_MODELS}")
    logger.info(f"⚡ Performance optimizations: Flash Attention, KV Cache, Quantization")

# Performance recommendation logging
logger.info("💡 Model Performance Estimates:")
for model_type, model_name in CURRENT_MODELS.items():
    if model_name in [model.name for model in OptimizedModelRegistry.MODELS.values()]:
        model_config = next(m for m in OptimizedModelRegistry.MODELS.values() if m.name == model_name)
        logger.info(f"  {model_type}: ~{model_config.tokens_per_second_estimate} tokens/s ({model_config.vram_requirement_gb}GB)")

logger.info("🚀 HASHIRU 6.1 Optimized Configuration Ready!")