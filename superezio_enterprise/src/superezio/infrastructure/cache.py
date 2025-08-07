"""In-memory cache implementation with TTL support."""

import asyncio
import time
from typing import Any, Optional, Dict, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import structlog
from collections import OrderedDict

from ..interfaces.repositories import CacheRepository

logger = structlog.get_logger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with TTL support."""
    value: Any
    created_at: float = field(default_factory=time.time)
    ttl: Optional[float] = None  # TTL in seconds
    access_count: int = field(default=0)
    last_accessed: float = field(default_factory=time.time)
    
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self) -> None:
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = time.time()


class InMemoryCacheRepository(CacheRepository):
    """In-memory cache with LRU eviction and TTL support."""
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None, cleanup_interval: int = 60):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
            "total_gets": 0,
            "total_sets": 0,
            "total_deletes": 0
        }
        
        # Start cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self) -> None:
        """Start the background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_entries())
            logger.info("Cache cleanup task started", interval=self.cleanup_interval)
    
    async def _cleanup_expired_entries(self) -> None:
        """Background task to clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                async with self._lock:
                    expired_keys = []
                    for key, entry in self._cache.items():
                        if entry.is_expired():
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        del self._cache[key]
                        self._stats["expirations"] += 1
                    
                    if expired_keys:
                        logger.debug("Cleaned up expired cache entries", 
                                   expired_count=len(expired_keys),
                                   remaining_count=len(self._cache))
            
            except asyncio.CancelledError:
                logger.info("Cache cleanup task cancelled")
                break
            except Exception as e:
                logger.error("Error in cache cleanup task", error=str(e))
                # Continue running despite errors
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        async with self._lock:
            self._stats["total_gets"] += 1
            
            entry = self._cache.get(key)
            if entry is None:
                self._stats["misses"] += 1
                logger.debug("Cache miss", key=key)
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self._stats["misses"] += 1
                self._stats["expirations"] += 1
                logger.debug("Cache entry expired", key=key)
                return None
            
            # Move to end (LRU)
            self._cache.move_to_end(key)
            entry.touch()
            
            self._stats["hits"] += 1
            logger.debug("Cache hit", key=key, access_count=entry.access_count)
            return entry.value
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        async with self._lock:
            self._stats["total_sets"] += 1
            
            # Use provided TTL or default
            effective_ttl = ttl if ttl is not None else self.default_ttl
            
            # Create new entry
            entry = CacheEntry(value=value, ttl=effective_ttl)
            
            # If key exists, update it
            if key in self._cache:
                self._cache[key] = entry
                self._cache.move_to_end(key)
                logger.debug("Cache entry updated", key=key, ttl=effective_ttl)
            else:
                # Add new entry
                self._cache[key] = entry
                logger.debug("Cache entry added", key=key, ttl=effective_ttl)
            
            # Evict if necessary
            while len(self._cache) > self.max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                self._stats["evictions"] += 1
                logger.debug("Cache entry evicted (LRU)", evicted_key=oldest_key)
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        async with self._lock:
            self._stats["total_deletes"] += 1
            
            if key in self._cache:
                del self._cache[key]
                logger.debug("Cache entry deleted", key=key)
                return True
            
            logger.debug("Cache entry not found for deletion", key=key)
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            entry_count = len(self._cache)
            self._cache.clear()
            logger.info("Cache cleared", cleared_count=entry_count)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": round(hit_rate, 2),
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "total_requests": total_requests,
                "evictions": self._stats["evictions"],
                "expirations": self._stats["expirations"],
                "total_operations": {
                    "gets": self._stats["total_gets"],
                    "sets": self._stats["total_sets"],
                    "deletes": self._stats["total_deletes"]
                },
                "memory_efficiency": round((len(self._cache) / self.max_size * 100), 2) if self.max_size > 0 else 0,
                "default_ttl": self.default_ttl,
                "cleanup_interval": self.cleanup_interval
            }
    
    async def get_keys(self) -> Set[str]:
        """Get all cache keys."""
        async with self._lock:
            return set(self._cache.keys())
    
    async def get_entry_info(self, key: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a cache entry."""
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            age_seconds = time.time() - entry.created_at
            time_since_access = time.time() - entry.last_accessed
            
            return {
                "key": key,
                "created_at": datetime.fromtimestamp(entry.created_at).isoformat(),
                "last_accessed": datetime.fromtimestamp(entry.last_accessed).isoformat(),
                "age_seconds": round(age_seconds, 2),
                "time_since_access": round(time_since_access, 2),
                "access_count": entry.access_count,
                "ttl": entry.ttl,
                "is_expired": entry.is_expired(),
                "value_type": type(entry.value).__name__
            }
    
    async def shutdown(self) -> None:
        """Shutdown cache and cleanup task."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self.clear()
        logger.info("Cache shutdown completed")


class NullCacheRepository(CacheRepository):
    """Null cache implementation that doesn't cache anything."""
    
    async def get(self, key: str) -> Optional[Any]:
        """Always returns None."""
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Does nothing."""
        pass
    
    async def delete(self, key: str) -> bool:
        """Always returns False."""
        return False
    
    async def clear(self) -> None:
        """Does nothing."""
        pass
    
    async def get_stats(self) -> Dict[str, Any]:
        """Returns empty stats."""
        return {
            "size": 0,
            "max_size": 0,
            "hit_rate": 0,
            "hits": 0,
            "misses": 0,
            "total_requests": 0,
            "evictions": 0,
            "expirations": 0,
            "total_operations": {"gets": 0, "sets": 0, "deletes": 0},
            "memory_efficiency": 0,
            "default_ttl": None,
            "cleanup_interval": 0
        }