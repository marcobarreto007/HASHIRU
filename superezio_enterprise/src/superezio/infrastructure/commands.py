"""Command repository implementation."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque
import structlog

from ..domain.models import CommandRequest, CommandResponse
from ..interfaces.repositories import CommandRepository

logger = structlog.get_logger(__name__)


class InMemoryCommandRepository(CommandRepository):
    """In-memory command repository with history management."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        
        self._requests: deque[CommandRequest] = deque(maxlen=max_history)
        self._responses: deque[CommandResponse] = deque(maxlen=max_history)
        self._request_index: Dict[str, CommandRequest] = {}
        self._response_index: Dict[str, CommandResponse] = {}
        
        self._lock = asyncio.Lock()
        
        # Statistics
        self._stats = {
            "total_requests": 0,
            "total_responses": 0,
            "successful_commands": 0,
            "failed_commands": 0,
            "average_execution_time": 0.0
        }
        
        logger.info("Command repository initialized", max_history=max_history)
    
    async def save_request(self, request: CommandRequest) -> None:
        """Save command request."""
        async with self._lock:
            self._requests.append(request)
            self._request_index[request.id] = request
            self._stats["total_requests"] += 1
            
            # Clean up old indices if we're at capacity
            if len(self._requests) >= self.max_history:
                # Remove old entries from index
                old_requests = list(self._requests)[:len(self._requests) - self.max_history + 1]
                for old_request in old_requests:
                    self._request_index.pop(old_request.id, None)
            
            logger.debug("Command request saved",
                        request_id=request.id,
                        command_type=request.command_type.value,
                        total_requests=self._stats["total_requests"])
    
    async def save_response(self, response: CommandResponse) -> None:
        """Save command response."""
        async with self._lock:
            self._responses.append(response)
            self._response_index[response.request_id] = response
            self._stats["total_responses"] += 1
            
            # Update success/failure statistics
            if response.success:
                self._stats["successful_commands"] += 1
            else:
                self._stats["failed_commands"] += 1
            
            # Update average execution time
            total_commands = self._stats["successful_commands"] + self._stats["failed_commands"]
            if total_commands > 0:
                current_avg = self._stats["average_execution_time"]
                self._stats["average_execution_time"] = (
                    (current_avg * (total_commands - 1) + response.execution_time_ms) / total_commands
                )
            
            # Clean up old indices if we're at capacity
            if len(self._responses) >= self.max_history:
                old_responses = list(self._responses)[:len(self._responses) - self.max_history + 1]
                for old_response in old_responses:
                    self._response_index.pop(old_response.request_id, None)
            
            logger.debug("Command response saved",
                        request_id=response.request_id,
                        success=response.success,
                        execution_time_ms=response.execution_time_ms,
                        total_responses=self._stats["total_responses"])
    
    async def get_request_history(self, limit: int = 100) -> List[CommandRequest]:
        """Get command request history."""
        async with self._lock:
            # Return most recent requests up to limit
            requests = list(self._requests)
            return requests[-limit:] if len(requests) > limit else requests
    
    async def get_response_history(self, limit: int = 100) -> List[CommandResponse]:
        """Get command response history."""
        async with self._lock:
            # Return most recent responses up to limit
            responses = list(self._responses)
            return responses[-limit:] if len(responses) > limit else responses
    
    async def get_request_by_id(self, request_id: str) -> Optional[CommandRequest]:
        """Get specific request by ID."""
        async with self._lock:
            return self._request_index.get(request_id)
    
    async def get_response_by_request_id(self, request_id: str) -> Optional[CommandResponse]:
        """Get response for specific request."""
        async with self._lock:
            return self._response_index.get(request_id)
    
    async def get_command_stats(self) -> Dict[str, Any]:
        """Get command statistics."""
        async with self._lock:
            recent_requests = list(self._requests)[-100:]  # Last 100 requests
            recent_responses = list(self._responses)[-100:]  # Last 100 responses
            
            # Analyze recent command types
            command_type_counts = {}
            for request in recent_requests:
                cmd_type = request.command_type.value
                command_type_counts[cmd_type] = command_type_counts.get(cmd_type, 0) + 1
            
            # Analyze recent execution times
            recent_execution_times = [r.execution_time_ms for r in recent_responses]
            avg_recent_time = sum(recent_execution_times) / len(recent_execution_times) if recent_execution_times else 0
            max_recent_time = max(recent_execution_times) if recent_execution_times else 0
            min_recent_time = min(recent_execution_times) if recent_execution_times else 0
            
            # Success rate calculation
            recent_successes = sum(1 for r in recent_responses if r.success)
            recent_success_rate = (recent_successes / len(recent_responses) * 100) if recent_responses else 0
            
            overall_success_rate = 0.0
            if self._stats["total_responses"] > 0:
                overall_success_rate = (self._stats["successful_commands"] / self._stats["total_responses"]) * 100
            
            return {
                "total_requests": self._stats["total_requests"],
                "total_responses": self._stats["total_responses"],
                "successful_commands": self._stats["successful_commands"],
                "failed_commands": self._stats["failed_commands"],
                "overall_success_rate": round(overall_success_rate, 2),
                "recent_success_rate": round(recent_success_rate, 2),
                "average_execution_time_ms": round(self._stats["average_execution_time"], 2),
                "recent_performance": {
                    "average_execution_time_ms": round(avg_recent_time, 2),
                    "max_execution_time_ms": round(max_recent_time, 2),
                    "min_execution_time_ms": round(min_recent_time, 2),
                    "sample_size": len(recent_execution_times)
                },
                "command_type_distribution": command_type_counts,
                "history_capacity": {
                    "max_history": self.max_history,
                    "current_requests": len(self._requests),
                    "current_responses": len(self._responses)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent command errors."""
        async with self._lock:
            error_responses = [
                {
                    "request_id": response.request_id,
                    "error_code": response.error_code,
                    "message": response.message,
                    "timestamp": response.timestamp.isoformat(),
                    "execution_time_ms": response.execution_time_ms
                }
                for response in self._responses
                if not response.success
            ]
            
            # Return most recent errors
            return error_responses[-limit:] if len(error_responses) > limit else error_responses
    
    async def cleanup_old_history(self, max_age_hours: int = 24) -> Dict[str, int]:
        """Clean up old command history."""
        async with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            # Count items before cleanup
            initial_requests = len(self._requests)
            initial_responses = len(self._responses)
            
            # Filter out old requests
            new_requests = deque([r for r in self._requests if r.timestamp >= cutoff_time], 
                               maxlen=self.max_history)
            new_responses = deque([r for r in self._responses if r.timestamp >= cutoff_time], 
                                maxlen=self.max_history)
            
            # Update collections
            self._requests = new_requests
            self._responses = new_responses
            
            # Rebuild indices
            self._request_index = {r.id: r for r in self._requests}
            self._response_index = {r.request_id: r for r in self._responses}
            
            removed_requests = initial_requests - len(self._requests)
            removed_responses = initial_responses - len(self._responses)
            
            logger.info("Command history cleaned up",
                       removed_requests=removed_requests,
                       removed_responses=removed_responses,
                       max_age_hours=max_age_hours)
            
            return {
                "removed_requests": removed_requests,
                "removed_responses": removed_responses,
                "remaining_requests": len(self._requests),
                "remaining_responses": len(self._responses)
            }