"""Circuit breaker implementation for fault tolerance."""

import asyncio
import time
from enum import Enum
from typing import Dict, Any, Optional, Callable, TypeVar, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import structlog

from ..interfaces.repositories import CircuitBreakerRepository

logger = structlog.get_logger(__name__)

T = TypeVar('T')


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"          # Blocking calls
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics."""
    name: str
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    total_requests: int = 0
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failure_count / self.total_requests * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        return 100.0 - self.failure_rate


class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        recovery_timeout: int = 30
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.recovery_timeout = recovery_timeout
        
        self.stats = CircuitBreakerStats(name=name)
        self._lock = asyncio.Lock()
        
        logger.info("Circuit breaker created",
                   name=name,
                   failure_threshold=failure_threshold,
                   timeout_seconds=timeout_seconds)
    
    async def call(self, func: Callable[[], Awaitable[T]]) -> T:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            await self._update_state()
            
            if self.stats.state == CircuitState.OPEN:
                logger.warning("Circuit breaker is OPEN, rejecting call", name=self.name)
                raise CircuitBreakerOpenError(f"Circuit breaker {self.name} is OPEN")
            
            self.stats.total_requests += 1
        
        # Execute the function
        start_time = time.time()
        try:
            result = await func()
            execution_time = time.time() - start_time
            
            async with self._lock:
                await self._record_success()
            
            logger.debug("Circuit breaker call succeeded",
                        name=self.name,
                        execution_time=execution_time)
            return result
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            async with self._lock:
                await self._record_failure()
            
            logger.error("Circuit breaker call failed",
                        name=self.name,
                        error=str(e),
                        execution_time=execution_time)
            raise
    
    async def _update_state(self) -> None:
        """Update circuit breaker state based on current conditions."""
        current_time = time.time()
        
        if self.stats.state == CircuitState.OPEN:
            # Check if we should transition to HALF_OPEN
            if current_time - self.stats.last_state_change >= self.timeout_seconds:
                await self._transition_to_half_open()
        
        elif self.stats.state == CircuitState.HALF_OPEN:
            # Check if we should close or open based on recent results
            if self.stats.success_count > 0:
                # We had some success in HALF_OPEN, close the circuit
                await self._transition_to_closed()
            elif (self.stats.last_failure_time and 
                  current_time - self.stats.last_failure_time <= self.recovery_timeout):
                # Recent failure in HALF_OPEN, open the circuit
                await self._transition_to_open()
    
    async def _record_success(self) -> None:
        """Record a successful operation."""
        self.stats.success_count += 1
        self.stats.last_success_time = time.time()
        
        # Reset failure count on success
        if self.stats.state == CircuitState.HALF_OPEN:
            await self._transition_to_closed()
        elif self.stats.state == CircuitState.CLOSED:
            # Reset failure count after successful operations 
            self.stats.failure_count = 0
        
        logger.debug("Success recorded", name=self.name, state=self.stats.state.value)
    
    async def _record_failure(self) -> None:
        """Record a failed operation."""
        self.stats.failure_count += 1
        self.stats.last_failure_time = time.time()
        
        # Check if we should transition to OPEN
        if (self.stats.state == CircuitState.CLOSED and 
            self.stats.failure_count >= self.failure_threshold):
            await self._transition_to_open()
        elif self.stats.state == CircuitState.HALF_OPEN:
            await self._transition_to_open()
        
        logger.debug("Failure recorded", 
                    name=self.name, 
                    failure_count=self.stats.failure_count,
                    state=self.stats.state.value)
    
    async def _transition_to_open(self) -> None:
        """Transition to OPEN state."""
        old_state = self.stats.state
        self.stats.state = CircuitState.OPEN
        self.stats.last_state_change = time.time()
        
        logger.warning("Circuit breaker transitioned to OPEN",
                      name=self.name,
                      previous_state=old_state.value,
                      failure_count=self.stats.failure_count)
    
    async def _transition_to_half_open(self) -> None:
        """Transition to HALF_OPEN state."""
        old_state = self.stats.state
        self.stats.state = CircuitState.HALF_OPEN
        self.stats.last_state_change = time.time()
        self.stats.success_count = 0  # Reset success count for testing
        
        logger.info("Circuit breaker transitioned to HALF_OPEN",
                   name=self.name,
                   previous_state=old_state.value)
    
    async def _transition_to_closed(self) -> None:
        """Transition to CLOSED state."""
        old_state = self.stats.state
        self.stats.state = CircuitState.CLOSED
        self.stats.last_state_change = time.time()
        self.stats.failure_count = 0  # Reset failure count
        
        logger.info("Circuit breaker transitioned to CLOSED",
                   name=self.name,
                   previous_state=old_state.value,
                   success_count=self.stats.success_count)
    
    async def force_open(self) -> None:
        """Force circuit breaker to OPEN state."""
        async with self._lock:
            await self._transition_to_open()
            logger.warning("Circuit breaker forced to OPEN", name=self.name)
    
    async def force_close(self) -> None:
        """Force circuit breaker to CLOSED state."""
        async with self._lock:
            await self._transition_to_closed()
            logger.info("Circuit breaker forced to CLOSED", name=self.name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.stats.name,
            "state": self.stats.state.value,
            "failure_count": self.stats.failure_count,
            "success_count": self.stats.success_count,
            "failure_rate": round(self.stats.failure_rate, 2),
            "success_rate": round(self.stats.success_rate, 2),
            "total_requests": self.stats.total_requests,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
            "last_state_change": self.stats.last_state_change,
            "configuration": {
                "failure_threshold": self.failure_threshold,
                "timeout_seconds": self.timeout_seconds,
                "recovery_timeout": self.recovery_timeout
            }
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class InMemoryCircuitBreakerRepository(CircuitBreakerRepository):
    """In-memory circuit breaker repository."""
    
    def __init__(
        self,
        default_failure_threshold: int = 5,
        default_timeout_seconds: int = 60,
        default_recovery_timeout: int = 30
    ):
        self.default_failure_threshold = default_failure_threshold
        self.default_timeout_seconds = default_timeout_seconds
        self.default_recovery_timeout = default_recovery_timeout
        
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
    
    def _get_circuit_breaker(self, circuit_name: str) -> CircuitBreaker:
        """Get or create circuit breaker."""
        if circuit_name not in self._circuit_breakers:
            self._circuit_breakers[circuit_name] = CircuitBreaker(
                name=circuit_name,
                failure_threshold=self.default_failure_threshold,
                timeout_seconds=self.default_timeout_seconds,
                recovery_timeout=self.default_recovery_timeout
            )
        return self._circuit_breakers[circuit_name]
    
    async def get_state(self, circuit_name: str) -> str:
        """Get circuit breaker state."""
        circuit = self._get_circuit_breaker(circuit_name)
        return circuit.stats.state.value
    
    async def record_success(self, circuit_name: str) -> None:
        """Record successful operation."""
        circuit = self._get_circuit_breaker(circuit_name)
        async with circuit._lock:
            await circuit._record_success()
    
    async def record_failure(self, circuit_name: str) -> None:
        """Record failed operation."""
        circuit = self._get_circuit_breaker(circuit_name)
        async with circuit._lock:
            await circuit._record_failure()
    
    async def force_open(self, circuit_name: str) -> None:
        """Force circuit breaker to open state."""
        circuit = self._get_circuit_breaker(circuit_name)
        await circuit.force_open()
    
    async def force_close(self, circuit_name: str) -> None:
        """Force circuit breaker to closed state."""
        circuit = self._get_circuit_breaker(circuit_name)
        await circuit.force_close()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        stats = {}
        for name, circuit in self._circuit_breakers.items():
            stats[name] = circuit.get_stats()
        
        return {
            "circuit_breakers": stats,
            "total_circuits": len(self._circuit_breakers),
            "default_config": {
                "failure_threshold": self.default_failure_threshold,
                "timeout_seconds": self.default_timeout_seconds,
                "recovery_timeout": self.default_recovery_timeout
            }
        }
    
    async def execute_with_circuit_breaker(
        self, 
        circuit_name: str, 
        func: Callable[[], Awaitable[T]]
    ) -> T:
        """Execute function with circuit breaker protection."""
        circuit = self._get_circuit_breaker(circuit_name)
        return await circuit.call(func)