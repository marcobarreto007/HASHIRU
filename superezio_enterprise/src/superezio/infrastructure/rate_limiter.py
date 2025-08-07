"""Rate limiter implementation using token bucket algorithm."""

import asyncio
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import structlog

from ..interfaces.repositories import RateLimiterRepository

logger = structlog.get_logger(__name__)


@dataclass
class TokenBucket:
    """Token bucket for rate limiting."""
    capacity: int
    refill_rate: float  # Tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(default_factory=time.time)
    total_requests: int = field(default=0)
    allowed_requests: int = field(default=0)
    rejected_requests: int = field(default=0)
    
    def __post_init__(self):
        self.tokens = float(self.capacity)
    
    def refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        
        if elapsed > 0:
            # Add tokens based on elapsed time
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens from the bucket."""
        self.refill()
        self.total_requests += 1
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            self.allowed_requests += 1
            return True
        else:
            self.rejected_requests += 1
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bucket statistics."""
        self.refill()  # Update current token count
        
        success_rate = 0.0
        if self.total_requests > 0:
            success_rate = (self.allowed_requests / self.total_requests) * 100
        
        return {
            "capacity": self.capacity,
            "current_tokens": round(self.tokens, 2),
            "refill_rate": self.refill_rate,
            "total_requests": self.total_requests,
            "allowed_requests": self.allowed_requests,
            "rejected_requests": self.rejected_requests,
            "success_rate": round(success_rate, 2),
            "last_refill": self.last_refill
        }


class InMemoryRateLimiterRepository(RateLimiterRepository):
    """In-memory rate limiter using token bucket algorithm."""
    
    def __init__(
        self,
        default_max_requests: int = 100,
        default_window_seconds: int = 60,
        default_burst_size: int = 10
    ):
        self.default_max_requests = default_max_requests
        self.default_window_seconds = default_window_seconds
        self.default_burst_size = default_burst_size
        
        # Calculate default refill rate (requests per second)
        self.default_refill_rate = default_max_requests / default_window_seconds
        
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = asyncio.Lock()
        
        logger.info("Rate limiter initialized",
                   max_requests=default_max_requests,
                   window_seconds=default_window_seconds,
                   burst_size=default_burst_size,
                   refill_rate=self.default_refill_rate)
    
    def _get_bucket(self, identifier: str) -> TokenBucket:
        """Get or create token bucket for identifier."""
        if identifier not in self._buckets:
            self._buckets[identifier] = TokenBucket(
                capacity=self.default_burst_size,
                refill_rate=self.default_refill_rate
            )
            logger.debug("Created new token bucket", identifier=identifier)
        
        return self._buckets[identifier]
    
    async def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed without consuming tokens."""
        async with self._lock:
            bucket = self._get_bucket(identifier)
            bucket.refill()
            return bucket.tokens >= 1
    
    async def record_request(self, identifier: str) -> None:
        """Record a request (consume token)."""
        async with self._lock:
            bucket = self._get_bucket(identifier)
            allowed = bucket.consume(1)
            
            if allowed:
                logger.debug("Request allowed", 
                           identifier=identifier,
                           remaining_tokens=bucket.tokens)
            else:
                logger.warning("Request rate limited", 
                             identifier=identifier,
                             total_requests=bucket.total_requests,
                             rejected_requests=bucket.rejected_requests)
    
    async def get_stats(self, identifier: str) -> Dict[str, Any]:
        """Get rate limiting stats for identifier."""
        async with self._lock:
            if identifier not in self._buckets:
                return {
                    "identifier": identifier,
                    "exists": False,
                    "message": "No requests recorded for this identifier"
                }
            
            bucket = self._buckets[identifier]
            stats = bucket.get_stats()
            stats["identifier"] = identifier
            stats["exists"] = True
            
            # Add time-based information
            stats["last_refill_ago"] = time.time() - bucket.last_refill
            stats["estimated_recovery_time"] = max(0, (1 - bucket.tokens) / bucket.refill_rate)
            
            return stats
    
    async def reset(self, identifier: str) -> None:
        """Reset rate limiting for identifier."""
        async with self._lock:
            if identifier in self._buckets:
                old_stats = self._buckets[identifier].get_stats()
                del self._buckets[identifier]
                logger.info("Rate limiter reset", 
                          identifier=identifier,
                          previous_stats=old_stats)
            else:
                logger.debug("Rate limiter reset requested for non-existent identifier", 
                           identifier=identifier)
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all identifiers."""
        async with self._lock:
            all_stats = {}
            total_buckets = len(self._buckets)
            total_requests = 0
            total_allowed = 0
            total_rejected = 0
            
            for identifier, bucket in self._buckets.items():
                bucket_stats = bucket.get_stats()
                all_stats[identifier] = bucket_stats
                
                total_requests += bucket_stats["total_requests"]
                total_allowed += bucket_stats["allowed_requests"]
                total_rejected += bucket_stats["rejected_requests"]
            
            overall_success_rate = 0.0
            if total_requests > 0:
                overall_success_rate = (total_allowed / total_requests) * 100
            
            return {
                "buckets": all_stats,
                "summary": {
                    "total_buckets": total_buckets,
                    "total_requests": total_requests,
                    "total_allowed": total_allowed,
                    "total_rejected": total_rejected,
                    "overall_success_rate": round(overall_success_rate, 2)
                },
                "configuration": {
                    "default_max_requests": self.default_max_requests,
                    "default_window_seconds": self.default_window_seconds,
                    "default_burst_size": self.default_burst_size,
                    "default_refill_rate": self.default_refill_rate
                }
            }
    
    async def cleanup_old_buckets(self, max_idle_time: int = 3600) -> int:
        """Clean up buckets that haven't been used recently."""
        async with self._lock:
            current_time = time.time()
            idle_buckets = []
            
            for identifier, bucket in self._buckets.items():
                if current_time - bucket.last_refill > max_idle_time:
                    idle_buckets.append(identifier)
            
            for identifier in idle_buckets:
                del self._buckets[identifier]
            
            if idle_buckets:
                logger.info("Cleaned up idle rate limiter buckets",
                          cleaned_count=len(idle_buckets),
                          max_idle_time=max_idle_time)
            
            return len(idle_buckets)


class RateLimitExceededError(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, identifier: str, retry_after: Optional[float] = None):
        self.identifier = identifier
        self.retry_after = retry_after
        message = f"Rate limit exceeded for {identifier}"
        if retry_after:
            message += f". Retry after {retry_after:.1f} seconds"
        super().__init__(message)


class RateLimitMiddleware:
    """Rate limit middleware for protecting functions."""
    
    def __init__(self, rate_limiter: RateLimiterRepository):
        self.rate_limiter = rate_limiter
    
    async def __call__(self, identifier: str, func, *args, **kwargs):
        """Execute function with rate limiting."""
        # Check if request is allowed
        if not await self.rate_limiter.is_allowed(identifier):
            stats = await self.rate_limiter.get_stats(identifier)
            retry_after = stats.get("estimated_recovery_time", 60)
            raise RateLimitExceededError(identifier, retry_after)
        
        # Record the request
        await self.rate_limiter.record_request(identifier)
        
        # Execute the function
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)


def rate_limit(identifier: str, rate_limiter: RateLimiterRepository):
    """Decorator for rate limiting functions."""
    def decorator(func):
        middleware = RateLimitMiddleware(rate_limiter)
        
        async def wrapper(*args, **kwargs):
            return await middleware(identifier, func, *args, **kwargs)
        
        return wrapper
    return decorator