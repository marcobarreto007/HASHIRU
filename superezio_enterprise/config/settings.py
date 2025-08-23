"""Configuration settings using Pydantic v2."""

from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="json", description="Log format: json or text")
    file_path: Optional[Path] = Field(default=None, description="Log file path")
    max_size: int = Field(default=10_000_000, description="Max log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup files")


class HardwareConfig(BaseModel):
    """Hardware monitoring configuration."""
    gpu_polling_interval: float = Field(default=5.0, description="GPU polling interval in seconds")
    temperature_threshold: float = Field(default=85.0, description="Temperature warning threshold")
    memory_threshold: float = Field(default=90.0, description="Memory usage warning threshold")
    enable_nvidia_ml: bool = Field(default=True, description="Enable NVIDIA ML monitoring")


class CacheConfig(BaseModel):
    """Cache configuration."""
    max_size: int = Field(default=1000, description="Maximum cache entries")
    ttl_seconds: int = Field(default=300, description="Time to live in seconds")
    cleanup_interval: int = Field(default=60, description="Cleanup interval in seconds")


class RateLimiterConfig(BaseModel):
    """Rate limiter configuration."""
    max_requests: int = Field(default=100, description="Maximum requests per window")
    window_seconds: int = Field(default=60, description="Rate limit window in seconds")
    burst_size: int = Field(default=10, description="Burst capacity")


class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""
    failure_threshold: int = Field(default=5, description="Failure threshold")
    timeout_seconds: int = Field(default=60, description="Circuit open timeout")
    recovery_timeout: int = Field(default=30, description="Recovery timeout")


class ChainlitConfig(BaseModel):
    """Chainlit UI configuration."""
    host: str = Field(default="0.0.0.0", description="Host address")
    port: int = Field(default=8000, description="Port number")
    debug: bool = Field(default=False, description="Debug mode")
    enable_auth: bool = Field(default=False, description="Enable authentication")
    session_timeout: int = Field(default=3600, description="Session timeout in seconds")


class AIModelConfig(BaseModel):
    """AI model configuration."""
    default_vram_mb: int = Field(default=4096, description="Default VRAM allocation per model in MB")
    core_models: List[str] = Field(
        default=["reasoning", "code", "conversation", "tools"],
        description="List of core AI models to load."
    )


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="forbid"
    )
    
    # Environment
    environment: str = Field(default="development", description="Environment: development, production, test")
    debug: bool = Field(default=True, description="Debug mode")
    
    # Application
    app_name: str = Field(default="SUPEREZIO Enterprise", description="Application name")
    version: str = Field(default="2.0.0", description="Application version")
    
    # Configuration sections
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    hardware: HardwareConfig = Field(default_factory=HardwareConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    rate_limiter: RateLimiterConfig = Field(default_factory=RateLimiterConfig)
    circuit_breaker: CircuitBreakerConfig = Field(default_factory=CircuitBreakerConfig)
    chainlit: ChainlitConfig = Field(default_factory=ChainlitConfig)
    ai_models: AIModelConfig = Field(default_factory=AIModelConfig)
    
    # Advanced settings
    async_pool_size: int = Field(default=10, description="Async pool size")
    health_check_interval: int = Field(default=30, description="Health check interval")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"
    
    @property
    def log_file_path(self) -> Optional[Path]:
        """Get log file path if configured."""
        if self.logging.file_path:
            return Path(self.logging.file_path)
        return None


# Global settings instance
settings = Settings()