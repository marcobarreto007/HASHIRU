"""Configuration repository implementation."""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import structlog

from ..interfaces.repositories import ConfigRepository

logger = structlog.get_logger(__name__)


class InMemoryConfigRepository(ConfigRepository):
    """In-memory configuration repository."""
    
    def __init__(self, initial_config: Optional[Dict[str, Any]] = None):
        self._config: Dict[str, Any] = initial_config or {}
        self._lock = asyncio.Lock()
        self._last_reload: Optional[datetime] = None
        
        # Metadata
        self._config_metadata: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Config repository initialized", 
                   config_keys=list(self._config.keys()))
    
    async def get_config(self, key: str) -> Optional[Any]:
        """Get configuration value."""
        async with self._lock:
            value = self._config.get(key)
            
            # Update access metadata
            if key in self._config_metadata:
                self._config_metadata[key]["last_accessed"] = datetime.utcnow().isoformat()
                self._config_metadata[key]["access_count"] += 1
            else:
                self._config_metadata[key] = {
                    "last_accessed": datetime.utcnow().isoformat(),
                    "access_count": 1,
                    "created_at": datetime.utcnow().isoformat()
                }
            
            logger.debug("Config value retrieved", key=key, value_type=type(value).__name__)
            return value
    
    async def set_config(self, key: str, value: Any) -> None:
        """Set configuration value."""
        async with self._lock:
            old_value = self._config.get(key)
            self._config[key] = value
            
            # Update metadata
            now = datetime.utcnow().isoformat()
            if key in self._config_metadata:
                self._config_metadata[key].update({
                    "last_modified": now,
                    "modification_count": self._config_metadata[key].get("modification_count", 0) + 1,
                    "previous_value": old_value
                })
            else:
                self._config_metadata[key] = {
                    "created_at": now,
                    "last_modified": now,
                    "modification_count": 1,
                    "access_count": 0,
                    "previous_value": old_value
                }
            
            logger.info("Config value set", 
                       key=key, 
                       value_type=type(value).__name__,
                       had_previous_value=old_value is not None)
    
    async def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration."""
        async with self._lock:
            return self._config.copy()
    
    async def reload_config(self) -> None:
        """Reload configuration from source."""
        # For in-memory implementation, this could reload from a file
        # or environment variables. For now, it's a no-op.
        async with self._lock:
            self._last_reload = datetime.utcnow()
            
            logger.info("Config reloaded", 
                       config_keys=list(self._config.keys()),
                       reload_time=self._last_reload.isoformat())
    
    async def get_config_metadata(self) -> Dict[str, Any]:
        """Get configuration metadata and statistics."""
        async with self._lock:
            total_keys = len(self._config)
            total_accesses = sum(meta.get("access_count", 0) for meta in self._config_metadata.values())
            total_modifications = sum(meta.get("modification_count", 0) for meta in self._config_metadata.values())
            
            # Find most and least accessed keys
            most_accessed = max(self._config_metadata.items(), 
                              key=lambda x: x[1].get("access_count", 0),
                              default=(None, {}))
            
            return {
                "total_keys": total_keys,
                "total_accesses": total_accesses,
                "total_modifications": total_modifications,
                "last_reload": self._last_reload.isoformat() if self._last_reload else None,
                "most_accessed_key": {
                    "key": most_accessed[0],
                    "access_count": most_accessed[1].get("access_count", 0)
                } if most_accessed[0] else None,
                "keys_metadata": self._config_metadata.copy(),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def backup_config(self) -> Dict[str, Any]:
        """Create a backup of current configuration."""
        async with self._lock:
            backup = {
                "config": self._config.copy(),
                "metadata": self._config_metadata.copy(),
                "backup_timestamp": datetime.utcnow().isoformat(),
                "total_keys": len(self._config)
            }
            
            logger.info("Config backup created", total_keys=len(self._config))
            return backup
    
    async def restore_config(self, backup: Dict[str, Any]) -> bool:
        """Restore configuration from backup."""
        try:
            async with self._lock:
                if "config" not in backup:
                    logger.error("Invalid backup format - missing 'config' key")
                    return False
                
                old_key_count = len(self._config)
                
                # Restore configuration
                self._config = backup["config"].copy()
                
                # Restore metadata if available
                if "metadata" in backup:
                    self._config_metadata = backup["metadata"].copy()
                else:
                    # Rebuild metadata
                    now = datetime.utcnow().isoformat()
                    self._config_metadata = {
                        key: {
                            "created_at": now,
                            "last_modified": now,
                            "modification_count": 1,
                            "access_count": 0,
                            "restored_from_backup": True
                        }
                        for key in self._config.keys()
                    }
                
                self._last_reload = datetime.utcnow()
                
                logger.info("Config restored from backup",
                           old_key_count=old_key_count,
                           new_key_count=len(self._config),
                           backup_timestamp=backup.get("backup_timestamp"))
                
                return True
        
        except Exception as e:
            logger.error("Failed to restore config from backup", error=str(e))
            return False
    
    async def clear_config(self) -> int:
        """Clear all configuration."""
        async with self._lock:
            cleared_count = len(self._config)
            self._config.clear()
            self._config_metadata.clear()
            
            logger.warning("All configuration cleared", cleared_count=cleared_count)
            return cleared_count
    
    async def search_config(self, pattern: str) -> Dict[str, Any]:
        """Search configuration keys by pattern."""
        async with self._lock:
            matching_keys = [key for key in self._config.keys() if pattern.lower() in key.lower()]
            
            results = {}
            for key in matching_keys:
                results[key] = {
                    "value": self._config[key],
                    "metadata": self._config_metadata.get(key, {})
                }
            
            logger.debug("Config search completed", 
                        pattern=pattern,
                        matches_found=len(matching_keys))
            
            return {
                "pattern": pattern,
                "matches_found": len(matching_keys),
                "results": results,
                "timestamp": datetime.utcnow().isoformat()
            }