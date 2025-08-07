"""Unit of Work implementation for managing repositories."""

import asyncio
from typing import Optional
import structlog

from ..interfaces.repositories import (
    UnitOfWork, HardwareRepository, CacheRepository, SessionRepository,
    CommandRepository, HealthCheckRepository, ConfigRepository,
    RateLimiterRepository, CircuitBreakerRepository
)

logger = structlog.get_logger(__name__)


class InMemoryUnitOfWork(UnitOfWork):
    """In-memory unit of work implementation."""
    
    def __init__(
        self,
        hardware_repo: HardwareRepository,
        cache_repo: CacheRepository,
        session_repo: SessionRepository,
        command_repo: CommandRepository,
        health_check_repo: HealthCheckRepository,
        config_repo: ConfigRepository,
        rate_limiter_repo: RateLimiterRepository,
        circuit_breaker_repo: CircuitBreakerRepository
    ):
        self._hardware_repo = hardware_repo
        self._cache_repo = cache_repo
        self._session_repo = session_repo
        self._command_repo = command_repo
        self._health_check_repo = health_check_repo
        self._config_repo = config_repo
        self._rate_limiter_repo = rate_limiter_repo
        self._circuit_breaker_repo = circuit_breaker_repo
        
        self._lock = asyncio.Lock()
        self._transaction_active = False
        
        logger.debug("Unit of Work initialized")
    
    async def __aenter__(self):
        """Enter async context."""
        await self._lock.acquire()
        self._transaction_active = True
        logger.debug("Unit of Work transaction started")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        try:
            if exc_type is None:
                await self.commit()
            else:
                await self.rollback()
                logger.error("Unit of Work transaction failed",
                           exception_type=exc_type.__name__ if exc_type else None,
                           error=str(exc_val) if exc_val else None)
        finally:
            self._transaction_active = False
            self._lock.release()
            logger.debug("Unit of Work transaction ended")
    
    async def commit(self) -> None:
        """Commit transaction."""
        if not self._transaction_active:
            logger.warning("Attempted to commit inactive transaction")
            return
        
        logger.debug("Unit of Work transaction committed")
        # In a real implementation with databases, this would commit the transaction
        # For in-memory implementations, this is mostly a no-op
    
    async def rollback(self) -> None:
        """Rollback transaction."""
        if not self._transaction_active:
            logger.warning("Attempted to rollback inactive transaction")
            return
        
        logger.debug("Unit of Work transaction rolled back")
        # In a real implementation with databases, this would rollback the transaction
        # For in-memory implementations, this is mostly a no-op
    
    @property
    def hardware(self) -> HardwareRepository:
        """Hardware repository."""
        return self._hardware_repo
    
    @property
    def cache(self) -> CacheRepository:
        """Cache repository."""
        return self._cache_repo
    
    @property
    def sessions(self) -> SessionRepository:
        """Session repository."""
        return self._session_repo
    
    @property
    def commands(self) -> CommandRepository:
        """Command repository."""
        return self._command_repo
    
    @property
    def health_check(self) -> HealthCheckRepository:
        """Health check repository."""
        return self._health_check_repo
    
    @property
    def config(self) -> ConfigRepository:
        """Config repository."""
        return self._config_repo
    
    @property
    def rate_limiter(self) -> RateLimiterRepository:
        """Rate limiter repository."""
        return self._rate_limiter_repo
    
    @property
    def circuit_breaker(self) -> CircuitBreakerRepository:
        """Circuit breaker repository."""
        return self._circuit_breaker_repo