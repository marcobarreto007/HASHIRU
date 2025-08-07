"""Health check implementation."""

import asyncio
import time
from typing import Dict, Any, List, Callable
from datetime import datetime
import structlog

from ..interfaces.repositories import HealthCheckRepository

logger = structlog.get_logger(__name__)


class HealthCheck:
    """Individual health check."""
    
    def __init__(self, name: str, check_func: Callable, timeout: float = 5.0):
        self.name = name
        self.check_func = check_func
        self.timeout = timeout
        self.last_result: Optional[bool] = None
        self.last_check_time: Optional[datetime] = None
        self.last_error: Optional[str] = None
    
    async def run(self) -> Dict[str, Any]:
        """Run the health check."""
        start_time = time.perf_counter()
        
        try:
            # Run check with timeout
            result = await asyncio.wait_for(self.check_func(), timeout=self.timeout)
            execution_time = (time.perf_counter() - start_time) * 1000
            
            self.last_result = bool(result)
            self.last_check_time = datetime.utcnow()
            self.last_error = None
            
            return {
                "name": self.name,
                "status": "healthy" if self.last_result else "unhealthy",
                "success": self.last_result,
                "execution_time_ms": round(execution_time, 2),
                "timestamp": self.last_check_time.isoformat(),
                "timeout": self.timeout
            }
        
        except asyncio.TimeoutError:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.last_result = False
            self.last_check_time = datetime.utcnow()
            self.last_error = f"Health check timed out after {self.timeout}s"
            
            logger.warning("Health check timed out",
                          name=self.name,
                          timeout=self.timeout,
                          execution_time_ms=execution_time)
            
            return {
                "name": self.name,
                "status": "timeout",
                "success": False,
                "error": self.last_error,
                "execution_time_ms": round(execution_time, 2),
                "timestamp": self.last_check_time.isoformat(),
                "timeout": self.timeout
            }
        
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            self.last_result = False
            self.last_check_time = datetime.utcnow()
            self.last_error = str(e)
            
            logger.error("Health check failed",
                        name=self.name,
                        error=str(e),
                        execution_time_ms=execution_time)
            
            return {
                "name": self.name,
                "status": "error",
                "success": False,
                "error": self.last_error,
                "execution_time_ms": round(execution_time, 2),
                "timestamp": self.last_check_time.isoformat(),
                "timeout": self.timeout
            }


class InMemoryHealthCheckRepository(HealthCheckRepository):
    """In-memory health check repository."""
    
    def __init__(self):
        self._checks: Dict[str, HealthCheck] = {}
        self._lock = asyncio.Lock()
        self._last_full_check: Optional[datetime] = None
        
        logger.info("Health check repository initialized")
    
    def register_check(self, name: str, check_func: Callable, timeout: float = 5.0) -> None:
        """Register a health check."""
        self._checks[name] = HealthCheck(name, check_func, timeout)
        logger.info("Health check registered", name=name, timeout=timeout)
    
    async def check_database_health(self) -> bool:
        """Check database health (simulation for in-memory implementation)."""
        # Simulate database health check
        await asyncio.sleep(0.1)  # Simulate DB query time
        return True  # In-memory is always "healthy"
    
    async def check_external_services(self) -> Dict[str, bool]:
        """Check external services health."""
        # Simulate external service checks
        services = {
            "nvidia_ml": True,  # Will be checked by hardware repository
            "system_metrics": True,  # Will be checked by hardware repository
            "cache_service": True,  # In-memory cache is always available
            "session_service": True,  # In-memory sessions are always available
        }
        
        # You could add real external service checks here
        # For example, checking if an API endpoint is reachable
        
        return services
    
    async def get_health_metrics(self) -> Dict[str, Any]:
        """Get comprehensive health metrics."""
        async with self._lock:
            self._last_full_check = datetime.utcnow()
            
            # Run all registered health checks
            check_results = []
            for check in self._checks.values():
                result = await check.run()
                check_results.append(result)
            
            # Run built-in checks
            db_healthy = await self.check_database_health()
            external_services = await self.check_external_services()
            
            # Calculate overall health
            all_checks_passed = all(result["success"] for result in check_results)
            all_services_healthy = all(external_services.values())
            overall_healthy = all_checks_passed and db_healthy and all_services_healthy
            
            # Performance metrics
            total_execution_time = sum(result["execution_time_ms"] for result in check_results)
            avg_execution_time = total_execution_time / len(check_results) if check_results else 0
            
            return {
                "overall_health": overall_healthy,
                "status": "healthy" if overall_healthy else "unhealthy",
                "timestamp": self._last_full_check.isoformat(),
                "checks": {
                    "registered_checks": check_results,
                    "database": {
                        "status": "healthy" if db_healthy else "unhealthy",
                        "success": db_healthy
                    },
                    "external_services": {
                        service: {"status": "healthy" if healthy else "unhealthy", "success": healthy}
                        for service, healthy in external_services.items()
                    }
                },
                "summary": {
                    "total_checks": len(check_results) + 1 + len(external_services),
                    "passed_checks": sum(1 for r in check_results if r["success"]) + (1 if db_healthy else 0) + sum(external_services.values()),
                    "failed_checks": sum(1 for r in check_results if not r["success"]) + (0 if db_healthy else 1) + sum(1 for v in external_services.values() if not v),
                    "average_execution_time_ms": round(avg_execution_time, 2),
                    "total_execution_time_ms": round(total_execution_time, 2)
                }
            }
    
    async def run_specific_check(self, check_name: str) -> Dict[str, Any]:
        """Run a specific health check."""
        async with self._lock:
            if check_name not in self._checks:
                return {
                    "name": check_name,
                    "status": "not_found",
                    "success": False,
                    "error": f"Health check '{check_name}' not found",
                    "available_checks": list(self._checks.keys())
                }
            
            check = self._checks[check_name]
            return await check.run()
    
    async def get_check_history(self, check_name: str) -> Dict[str, Any]:
        """Get history for a specific check."""
        async with self._lock:
            if check_name not in self._checks:
                return {
                    "error": f"Health check '{check_name}' not found",
                    "available_checks": list(self._checks.keys())
                }
            
            check = self._checks[check_name]
            return {
                "name": check_name,
                "last_result": check.last_result,
                "last_check_time": check.last_check_time.isoformat() if check.last_check_time else None,
                "last_error": check.last_error,
                "timeout": check.timeout,
                "status": "healthy" if check.last_result else "unhealthy"
            }
    
    async def register_auto_checks(self, hardware_repo, cache_repo) -> None:
        """Register automatic health checks for repositories."""
        
        async def hardware_check():
            """Check hardware repository health."""
            return await hardware_repo.is_healthy()
        
        async def cache_check():
            """Check cache repository health."""
            stats = await cache_repo.get_stats()
            return stats.get("size", 0) >= 0  # Basic health indicator
        
        self.register_check("hardware", hardware_check, timeout=3.0)
        self.register_check("cache", cache_check, timeout=1.0)
        
        logger.info("Auto health checks registered", 
                   checks=["hardware", "cache"])


class HealthMonitor:
    """Health monitoring service."""
    
    def __init__(self, health_repo: HealthCheckRepository, check_interval: int = 30):
        self.health_repo = health_repo
        self.check_interval = check_interval
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False
        self._health_history: List[Dict[str, Any]] = []
        self._max_history = 100
        
        logger.info("Health monitor initialized", check_interval=check_interval)
    
    async def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self._is_monitoring:
            logger.warning("Health monitoring already started")
            return
        
        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self._is_monitoring = False
        
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._is_monitoring:
            try:
                # Perform health check
                health_metrics = await self.health_repo.get_health_metrics()
                
                # Store in history
                self._health_history.append(health_metrics)
                if len(self._health_history) > self._max_history:
                    self._health_history.pop(0)
                
                # Log if unhealthy
                if not health_metrics["overall_health"]:
                    logger.warning("System health check failed", 
                                 failed_checks=health_metrics["summary"]["failed_checks"])
                
                await asyncio.sleep(self.check_interval)
            
            except asyncio.CancelledError:
                logger.info("Health monitoring loop cancelled")
                break
            except Exception as e:
                logger.error("Error in health monitoring loop", error=str(e))
                await asyncio.sleep(5)  # Short delay before retrying
    
    async def get_health_trend(self) -> Dict[str, Any]:
        """Get health trend analysis."""
        if not self._health_history:
            return {
                "status": "no_data",
                "message": "No health history available"
            }
        
        recent_checks = self._health_history[-10:]  # Last 10 checks
        healthy_count = sum(1 for check in recent_checks if check["overall_health"])
        
        trend = "stable"
        if len(recent_checks) >= 5:
            first_half = recent_checks[:len(recent_checks)//2]
            second_half = recent_checks[len(recent_checks)//2:]
            
            first_half_healthy = sum(1 for check in first_half if check["overall_health"]) / len(first_half)
            second_half_healthy = sum(1 for check in second_half if check["overall_health"]) / len(second_half)
            
            if second_half_healthy > first_half_healthy + 0.2:
                trend = "improving"
            elif second_half_healthy < first_half_healthy - 0.2:
                trend = "degrading"
        
        return {
            "trend": trend,
            "recent_health_rate": round((healthy_count / len(recent_checks)) * 100, 2),
            "total_checks": len(self._health_history),
            "recent_checks": len(recent_checks),
            "is_monitoring": self._is_monitoring,
            "last_check": self._health_history[-1]["timestamp"] if self._health_history else None
        }