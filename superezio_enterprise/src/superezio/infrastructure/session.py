"""Session management implementation."""

import asyncio
import time
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import structlog

from ..interfaces.repositories import SessionRepository

logger = structlog.get_logger(__name__)


@dataclass
class SessionData:
    """Session data container."""
    session_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    
    def is_expired(self, default_timeout: int = 3600) -> bool:
        """Check if session is expired."""
        if self.expires_at:
            return time.time() > self.expires_at
        
        # Use last accessed time with default timeout
        return time.time() - self.last_accessed > default_timeout
    
    def touch(self) -> None:
        """Update last accessed time."""
        self.last_accessed = time.time()
    
    def set_expiry(self, timeout_seconds: int) -> None:
        """Set session expiry time."""
        self.expires_at = time.time() + timeout_seconds
    
    def get_age_seconds(self) -> float:
        """Get session age in seconds."""
        return time.time() - self.created_at
    
    def get_idle_seconds(self) -> float:
        """Get seconds since last access."""
        return time.time() - self.last_accessed


class InMemorySessionRepository(SessionRepository):
    """In-memory session repository with TTL and cleanup."""
    
    def __init__(self, default_timeout: int = 3600, cleanup_interval: int = 300):
        self.default_timeout = default_timeout
        self.cleanup_interval = cleanup_interval
        
        self._sessions: Dict[str, SessionData] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            "total_sessions_created": 0,
            "total_sessions_expired": 0,
            "total_sessions_deleted": 0,
            "total_gets": 0,
            "total_sets": 0
        }
        
        # Start cleanup task
        self._start_cleanup_task()
        
        logger.info("Session repository initialized",
                   default_timeout=default_timeout,
                   cleanup_interval=cleanup_interval)
    
    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions_task())
            logger.info("Session cleanup task started")
    
    async def _cleanup_expired_sessions_task(self) -> None:
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                expired_count = await self.cleanup_expired_sessions()
                
                if expired_count > 0:
                    logger.info("Cleaned up expired sessions", expired_count=expired_count)
            
            except asyncio.CancelledError:
                logger.info("Session cleanup task cancelled")
                break
            except Exception as e:
                logger.error("Error in session cleanup task", error=str(e))
                # Continue running despite errors
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        async with self._lock:
            self._stats["total_gets"] += 1
            
            session = self._sessions.get(session_id)
            if session is None:
                logger.debug("Session not found", session_id=session_id)
                return None
            
            if session.is_expired(self.default_timeout):
                # Session expired, remove it
                del self._sessions[session_id]
                self._stats["total_sessions_expired"] += 1
                logger.debug("Session expired and removed", 
                           session_id=session_id,
                           age_seconds=session.get_age_seconds())
                return None
            
            # Update access time
            session.touch()
            
            logger.debug("Session retrieved", 
                        session_id=session_id,
                        data_keys=list(session.data.keys()),
                        age_seconds=session.get_age_seconds())
            
            return session.data.copy()
    
    async def set_session(self, session_id: str, data: Dict[str, Any]) -> None:
        """Set session data."""
        async with self._lock:
            self._stats["total_sets"] += 1
            
            if session_id in self._sessions:
                # Update existing session
                session = self._sessions[session_id]
                session.data = data.copy()
                session.touch()
                logger.debug("Session updated", 
                           session_id=session_id,
                           data_keys=list(data.keys()))
            else:
                # Create new session
                session = SessionData(
                    session_id=session_id,
                    data=data.copy()
                )
                session.set_expiry(self.default_timeout)
                self._sessions[session_id] = session
                self._stats["total_sessions_created"] += 1
                
                logger.debug("New session created", 
                           session_id=session_id,
                           data_keys=list(data.keys()),
                           expires_in=self.default_timeout)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session."""
        async with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                del self._sessions[session_id]
                self._stats["total_sessions_deleted"] += 1
                
                logger.debug("Session deleted", 
                           session_id=session_id,
                           age_seconds=session.get_age_seconds())
                return True
            
            logger.debug("Session not found for deletion", session_id=session_id)
            return False
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions, return count of deleted sessions."""
        async with self._lock:
            expired_sessions = []
            current_time = time.time()
            
            for session_id, session in self._sessions.items():
                if session.is_expired(self.default_timeout):
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            for session_id in expired_sessions:
                del self._sessions[session_id]
                self._stats["total_sessions_expired"] += 1
            
            if expired_sessions:
                logger.debug("Expired sessions cleaned up", 
                           expired_count=len(expired_sessions),
                           remaining_sessions=len(self._sessions))
            
            return len(expired_sessions)
    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed session information without the data."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            
            return {
                "session_id": session_id,
                "created_at": datetime.fromtimestamp(session.created_at).isoformat(),
                "last_accessed": datetime.fromtimestamp(session.last_accessed).isoformat(),
                "expires_at": datetime.fromtimestamp(session.expires_at).isoformat() if session.expires_at else None,
                "age_seconds": session.get_age_seconds(),
                "idle_seconds": session.get_idle_seconds(),
                "is_expired": session.is_expired(self.default_timeout),
                "data_size": len(session.data),
                "data_keys": list(session.data.keys())
            }
    
    async def get_all_sessions_info(self) -> Dict[str, Any]:
        """Get information about all sessions."""
        async with self._lock:
            sessions_info = {}
            active_sessions = 0
            expired_sessions = 0
            total_data_size = 0
            
            for session_id, session in self._sessions.items():
                if session.is_expired(self.default_timeout):
                    expired_sessions += 1
                else:
                    active_sessions += 1
                
                total_data_size += len(session.data)
                
                sessions_info[session_id] = {
                    "created_at": datetime.fromtimestamp(session.created_at).isoformat(),
                    "last_accessed": datetime.fromtimestamp(session.last_accessed).isoformat(),
                    "age_seconds": session.get_age_seconds(),
                    "idle_seconds": session.get_idle_seconds(),
                    "is_expired": session.is_expired(self.default_timeout),
                    "data_size": len(session.data)
                }
            
            return {
                "total_sessions": len(self._sessions),
                "active_sessions": active_sessions,
                "expired_sessions": expired_sessions,
                "total_data_size": total_data_size,
                "sessions": sessions_info,
                "configuration": {
                    "default_timeout": self.default_timeout,
                    "cleanup_interval": self.cleanup_interval
                },
                "statistics": self._stats.copy(),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def extend_session(self, session_id: str, additional_seconds: int = None) -> bool:
        """Extend session timeout."""
        async with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            
            if session.is_expired(self.default_timeout):
                return False
            
            # Extend session
            extension = additional_seconds or self.default_timeout
            session.set_expiry(extension)
            session.touch()
            
            logger.debug("Session extended", 
                        session_id=session_id,
                        extension_seconds=extension)
            
            return True
    
    async def get_active_session_count(self) -> int:
        """Get count of active (non-expired) sessions."""
        async with self._lock:
            active_count = 0
            for session in self._sessions.values():
                if not session.is_expired(self.default_timeout):
                    active_count += 1
            return active_count
    
    async def shutdown(self) -> None:
        """Shutdown session repository."""
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clear all sessions
        async with self._lock:
            session_count = len(self._sessions)
            self._sessions.clear()
        
        logger.info("Session repository shutdown", cleared_sessions=session_count)


class SessionManager:
    """High-level session manager."""
    
    def __init__(self, session_repo: SessionRepository):
        self.session_repo = session_repo
        self.logger = structlog.get_logger(self.__class__.__name__)
    
    async def create_session(self, session_id: str, initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new session."""
        data = initial_data or {}
        data["created_at"] = datetime.utcnow().isoformat()
        data["user_agent"] = "SUPEREZIO Enterprise"
        
        await self.session_repo.set_session(session_id, data)
        
        self.logger.info("Session created", session_id=session_id)
        
        return {
            "session_id": session_id,
            "status": "created",
            "data": data
        }
    
    async def get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        """Get existing session or create new one."""
        session_data = await self.session_repo.get_session(session_id)
        
        if session_data is None:
            return await self.create_session(session_id)
        
        return {
            "session_id": session_id,
            "status": "existing",
            "data": session_data
        }
    
    async def update_session_data(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data."""
        session_data = await self.session_repo.get_session(session_id)
        
        if session_data is None:
            self.logger.warning("Attempted to update non-existent session", session_id=session_id)
            return False
        
        # Merge updates
        session_data.update(updates)
        session_data["last_updated"] = datetime.utcnow().isoformat()
        
        await self.session_repo.set_session(session_id, session_data)
        
        self.logger.debug("Session data updated", 
                         session_id=session_id,
                         update_keys=list(updates.keys()))
        
        return True
    
    async def get_session_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session summary without full data."""
        return await self.session_repo.get_session_info(session_id)