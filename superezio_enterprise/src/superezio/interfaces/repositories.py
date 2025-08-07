"""Repository interfaces (ports) for the application."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, AsyncContextManager
from datetime import datetime

from ..domain.models import SystemStatus, GPUInfo, CommandRequest, CommandResponse


class HardwareRepository(ABC):
    """Hardware repository interface."""
    
    @abstractmethod
    async def get_gpu_info(self) -> List[GPUInfo]:
        """Get information about all GPUs."""
        pass
    
    @abstractmethod
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics (CPU, memory, disk)."""
        pass
    
    @abstractmethod
    async def is_healthy(self) -> bool:
        """Check if hardware monitoring is healthy."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize hardware monitoring."""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Shutdown hardware monitoring."""
        pass


class CacheRepository(ABC):
    """Cache repository interface."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all cache entries."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        pass


class SessionRepository(ABC):
    """Session repository interface."""
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        pass
    
    @abstractmethod
    async def set_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Set session data."""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        pass
    
    @abstractmethod
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions, return count of deleted sessions."""
        pass


class CommandRepository(ABC):
    """Command repository interface."""
    
    @abstractmethod
    async def save_request(self, request: CommandRequest) -> None:
        """Save command request."""
        pass
    
    @abstractmethod
    async def save_response(self, response: CommandResponse) -> None:
        """Save command response."""
        pass
    
    @abstractmethod
    async def get_request_history(self, limit: int = 100) -> List[CommandRequest]:
        """Get command request history."""
        pass
    
    @abstractmethod
    async def get_response_history(self, limit: int = 100) -> List[CommandResponse]:
        """Get command response history."""
        pass


class HealthCheckRepository(ABC):
    """Health check repository interface."""
    
    @abstractmethod
    async def check_database_health(self) -> bool:
        """Check database health."""
        pass
    
    @abstractmethod
    async def check_external_services(self) -> Dict[str, bool]:
        """Check external services health."""
        pass
    
    @abstractmethod
    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get comprehensive health metrics."""
        pass


class ConfigRepository(ABC):
    """Configuration repository interface."""
    
    @abstractmethod
    async def get_config(self, key: str) -> Optional[Any]:
        """Get configuration value."""
        pass
    
    @abstractmethod
    async def set_config(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass
    
    @abstractmethod
    async def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration."""
        pass
    
    @abstractmethod
    async def reload_config(self) -> None:
        """Reload configuration from source."""
        pass


class RateLimiterRepository(ABC):
    """Rate limiter repository interface."""
    
    @abstractmethod
    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed."""
        pass
    
    @abstractmethod
    async def record_request(self, identifier: str) -> None:
        """Record a request."""
        pass
    
    @abstractmethod
    async def get_stats(self, identifier: str) -> Dict[str, Any]:
        """Get rate limiting stats for identifier."""
        pass
    
    @abstractmethod
    async def reset(self, identifier: str) -> None:
        """Reset rate limiting for identifier."""
        pass


class CircuitBreakerRepository(ABC):
    """Circuit breaker repository interface."""
    
    @abstractmethod
    async def get_state(self, circuit_name: str) -> str:
        """Get circuit breaker state."""
        pass
    
    @abstractmethod
    async def record_success(self, circuit_name: str) -> None:
        """Record successful operation."""
        pass
    
    @abstractmethod
    async def record_failure(self, circuit_name: str) -> None:
        """Record failed operation."""
        pass
    
    @abstractmethod
    async def force_open(self, circuit_name: str) -> None:
        """Force circuit breaker to open state."""
        pass
    
    @abstractmethod
    async def force_close(self, circuit_name: str) -> None:
        """Force circuit breaker to closed state."""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        pass


class UnitOfWork(ABC):
    """Unit of work interface for managing transactions."""
    
    @abstractmethod
    async def __aenter__(self):
        """Enter async context."""
        pass
    
    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit transaction."""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback transaction."""
        pass
    
    # Repository properties
    @property
    @abstractmethod
    def hardware(self) -> HardwareRepository:
        """Hardware repository."""
        pass
    
    @property
    @abstractmethod
    def cache(self) -> CacheRepository:
        """Cache repository."""
        pass
    
    @property
    @abstractmethod
    def sessions(self) -> SessionRepository:
        """Session repository."""
        pass
    
    @property
    @abstractmethod
    def commands(self) -> CommandRepository:
        """Command repository."""
        pass
    
    @property
    @abstractmethod
    def health_check(self) -> HealthCheckRepository:
        """Health check repository."""
        pass
    
    @property
    @abstractmethod
    def config(self) -> ConfigRepository:
        """Config repository."""
        pass
    
    @property
    @abstractmethod
    def rate_limiter(self) -> RateLimiterRepository:
        """Rate limiter repository."""
        pass
    
    @property
    @abstractmethod
    def circuit_breaker(self) -> CircuitBreakerRepository:
        """Circuit breaker repository."""
        pass