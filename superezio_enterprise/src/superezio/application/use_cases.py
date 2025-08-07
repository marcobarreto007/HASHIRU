"""Application use cases implementing business logic."""

import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

from ..domain.models import (
    SystemStatus, SystemStatusEnum, CommandRequest, CommandResponse,
    CommandTypeEnum, GPUInfo, SystemMetrics, DomainEvent,
    SystemStartedEvent, GPUStatusChangedEvent, CommandExecutedEvent,
    SystemErrorEvent
)
from ..domain.events import event_bus
from ..interfaces.repositories import UnitOfWork

logger = structlog.get_logger(__name__)


class SystemUseCase:
    """Main system use case orchestrating all operations."""
    
    def __init__(self, uow: UnitOfWork):
        self.uow = uow
        self._startup_time = datetime.utcnow()
        self._last_health_check: Optional[datetime] = None
        logger.info("System use case initialized")
    
    async def start_system(self) -> Dict[str, Any]:
        """Start the system and initialize all components."""
        start_time = time.perf_counter()
        
        try:
            async with self.uow:
                # Initialize hardware monitoring
                await self.uow.hardware.initialize()
                
                # Perform initial health check
                health_status = await self._perform_health_check()
                
                # Clear old cache entries
                await self.uow.cache.clear()
                
                # Publish system started event
                await event_bus.publish(
                    SystemStartedEvent(
                        name="system.started",
                        payload={
                            "startup_time": self._startup_time.isoformat(),
                            "health_status": health_status
                        }
                    )
                )
                
                execution_time = (time.perf_counter() - start_time) * 1000
                
                logger.info("System started successfully", 
                          execution_time_ms=execution_time,
                          health_status=health_status)
                
                return {
                    "status": "success",
                    "message": "System started successfully",
                    "startup_time": self._startup_time.isoformat(),
                    "execution_time_ms": execution_time,
                    "health_status": health_status
                }
        
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            
            # Publish error event
            await event_bus.publish(
                SystemErrorEvent(
                    name="system.error",
                    payload={
                        "operation": "start_system",
                        "error": str(e),
                        "execution_time_ms": execution_time
                    }
                )
            )
            
            logger.error("Failed to start system", 
                        error=str(e),
                        execution_time_ms=execution_time)
            
            return {
                "status": "error",
                "message": f"Failed to start system: {str(e)}",
                "execution_time_ms": execution_time
            }
    
    async def execute_command(self, request: CommandRequest) -> CommandResponse:
        """Execute a command and return response."""
        start_time = time.perf_counter()
        
        logger.info("Executing command",
                   command_type=request.command_type.value,
                   request_id=request.id,
                   user_id=request.user_id)
        
        try:
            # Save request
            async with self.uow:
                await self.uow.commands.save_request(request)
            
            # Route to appropriate handler
            if request.command_type == CommandTypeEnum.SYSTEM_INFO:
                data = await self._get_system_info()
            elif request.command_type == CommandTypeEnum.GPU_STATUS:
                data = await self._get_gpu_status()
            elif request.command_type == CommandTypeEnum.HARDWARE_MONITOR:
                data = await self._get_hardware_monitor()
            elif request.command_type == CommandTypeEnum.CACHE_STATS:
                data = await self._get_cache_stats()
            elif request.command_type == CommandTypeEnum.HEALTH_CHECK:
                data = await self._perform_health_check()
            elif request.command_type == CommandTypeEnum.RESET_SYSTEM:
                data = await self._reset_system()
            else:
                data = await self._handle_custom_command(request)
            
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            
            response = CommandResponse(
                request_id=request.id,
                success=True,
                data=data,
                message="Command executed successfully",
                execution_time_ms=execution_time_ms
            )
            
            # Save response
            async with self.uow:
                await self.uow.commands.save_response(response)
            
            # Publish command executed event
            await event_bus.publish(
                CommandExecutedEvent(
                    name="command.executed",
                    payload={
                        "command_type": request.command_type.value,
                        "request_id": request.id,
                        "success": True,
                        "execution_time_ms": execution_time_ms
                    }
                )
            )
            
            logger.info("Command executed successfully",
                       command_type=request.command_type.value,
                       request_id=request.id,
                       execution_time_ms=execution_time_ms)
            
            return response
        
        except Exception as e:
            execution_time_ms = (time.perf_counter() - start_time) * 1000
            
            response = CommandResponse(
                request_id=request.id,
                success=False,
                message=f"Command execution failed: {str(e)}",
                error_code="EXECUTION_ERROR",
                execution_time_ms=execution_time_ms
            )
            
            # Save error response
            try:
                async with self.uow:
                    await self.uow.commands.save_response(response)
            except Exception as save_error:
                logger.error("Failed to save error response", 
                           save_error=str(save_error))
            
            # Publish error event
            await event_bus.publish(
                SystemErrorEvent(
                    name="system.error",
                    payload={
                        "operation": "execute_command",
                        "command_type": request.command_type.value,
                        "request_id": request.id,
                        "error": str(e),
                        "execution_time_ms": execution_time_ms
                    }
                )
            )
            
            logger.error("Command execution failed",
                        command_type=request.command_type.value,
                        request_id=request.id,
                        error=str(e),
                        execution_time_ms=execution_time_ms)
            
            return response
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        async with self.uow:
            gpus = await self.uow.hardware.get_gpu_info()
            system_metrics = await self.uow.hardware.get_system_metrics()
            cache_stats = await self.uow.cache.get_stats()
            
            return {
                "gpus": [gpu.model_dump() for gpu in gpus],
                "system_metrics": system_metrics,
                "cache_stats": cache_stats,
                "uptime": (datetime.utcnow() - self._startup_time).total_seconds(),
                "startup_time": self._startup_time.isoformat(),
                "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None
            }
    
    async def _get_gpu_status(self) -> Dict[str, Any]:
        """Get detailed GPU status."""
        async with self.uow:
            gpus = await self.uow.hardware.get_gpu_info()
            
            # Analyze GPU health
            alerts = []
            warnings = []
            
            for gpu in gpus:
                if gpu.is_overheating:
                    alerts.append(f"GPU {gpu.id} ({gpu.name}) overheating: {gpu.temperature}°C")
                elif gpu.temperature > 75:
                    warnings.append(f"GPU {gpu.id} ({gpu.name}) running warm: {gpu.temperature}°C")
                
                if gpu.is_memory_critical:
                    alerts.append(f"GPU {gpu.id} ({gpu.name}) memory critical: {gpu.memory_usage_percentage:.1f}%")
                elif gpu.memory_usage_percentage > 80:
                    warnings.append(f"GPU {gpu.id} ({gpu.name}) memory high: {gpu.memory_usage_percentage:.1f}%")
            
            total_memory = sum(gpu.memory_total for gpu in gpus)
            used_memory = sum(gpu.memory_used for gpu in gpus)
            avg_utilization = sum(gpu.gpu_utilization for gpu in gpus) / len(gpus) if gpus else 0
            avg_temperature = sum(gpu.temperature for gpu in gpus) / len(gpus) if gpus else 0
            total_power = sum(gpu.power_draw for gpu in gpus)
            
            # Publish GPU status change event if there are alerts
            if alerts:
                await event_bus.publish(
                    GPUStatusChangedEvent(
                        name="gpu.status_changed",
                        payload={
                            "gpu_count": len(gpus),
                            "alerts": alerts,
                            "warnings": warnings,
                            "avg_temperature": avg_temperature
                        }
                    )
                )
            
            return {
                "gpu_count": len(gpus),
                "gpus": [gpu.model_dump() for gpu in gpus],
                "summary": {
                    "total_memory_mb": total_memory,
                    "used_memory_mb": used_memory,
                    "free_memory_mb": total_memory - used_memory,
                    "memory_usage_percentage": round((used_memory / total_memory * 100), 2) if total_memory > 0 else 0,
                    "average_utilization": round(avg_utilization, 2),
                    "average_temperature": round(avg_temperature, 2),
                    "total_power_draw": round(total_power, 2)
                },
                "alerts": alerts,
                "warnings": warnings,
                "health_status": "critical" if alerts else ("warning" if warnings else "healthy")
            }
    
    async def _get_hardware_monitor(self) -> Dict[str, Any]:
        """Get comprehensive hardware monitoring data."""
        async with self.uow:
            gpus = await self.uow.hardware.get_gpu_info()
            system_metrics = await self.uow.hardware.get_system_metrics()
            hardware_health = await self.uow.hardware.is_healthy()
            
            # Additional monitoring data
            monitoring_data = {
                "hardware_health": hardware_health,
                "monitoring_active": hardware_health,
                "gpus": [gpu.model_dump() for gpu in gpus],
                "system_metrics": system_metrics,
                "timestamp": datetime.utcnow().isoformat(),
                "monitoring_duration": (datetime.utcnow() - self._startup_time).total_seconds()
            }
            
            # Add performance metrics
            if gpus:
                monitoring_data["performance"] = {
                    "peak_temperature": max(gpu.temperature for gpu in gpus),
                    "peak_memory_usage": max(gpu.memory_usage_percentage for gpu in gpus),
                    "peak_utilization": max(gpu.gpu_utilization for gpu in gpus),
                    "total_vram": sum(gpu.memory_total for gpu in gpus),
                    "available_vram": sum(gpu.memory_free for gpu in gpus)
                }
            
            return monitoring_data
    
    async def _perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        self._last_health_check = datetime.utcnow()
        
        health_status = {
            "overall_status": SystemStatusEnum.HEALTHY.value,
            "timestamp": self._last_health_check.isoformat(),
            "components": {},
            "alerts": [],
            "warnings": []
        }
        
        try:
            async with self.uow:
                # Check hardware
                hardware_health = await self.uow.hardware.is_healthy()
                health_status["components"]["hardware"] = {
                    "status": "healthy" if hardware_health else "error",
                    "details": "Hardware monitoring operational" if hardware_health else "Hardware monitoring failed"
                }
                
                if not hardware_health:
                    health_status["alerts"].append("Hardware monitoring is not operational")
                    health_status["overall_status"] = SystemStatusEnum.ERROR.value
                
                # Check cache
                cache_stats = await self.uow.cache.get_stats()
                cache_healthy = cache_stats.get("size", 0) >= 0
                health_status["components"]["cache"] = {
                    "status": "healthy" if cache_healthy else "error",
                    "details": f"Cache: {cache_stats.get('size', 0)} entries, {cache_stats.get('hit_rate', 0)}% hit rate"
                }
                
                # Check rate limiter
                try:
                    rate_limiter_stats = await self.uow.rate_limiter.get_stats("health_check")
                    health_status["components"]["rate_limiter"] = {
                        "status": "healthy",
                        "details": "Rate limiter operational"
                    }
                except Exception as e:
                    health_status["components"]["rate_limiter"] = {
                        "status": "error",
                        "details": f"Rate limiter error: {str(e)}"
                    }
                    health_status["warnings"].append("Rate limiter issues detected")
                
                # Check circuit breakers
                try:
                    cb_stats = await self.uow.circuit_breaker.get_stats()
                    open_circuits = [name for name, stats in cb_stats.get("circuit_breakers", {}).items() 
                                   if stats.get("state") == "open"]
                    
                    health_status["components"]["circuit_breaker"] = {
                        "status": "warning" if open_circuits else "healthy",
                        "details": f"Circuit breakers: {len(open_circuits)} open" if open_circuits else "All circuits healthy"
                    }
                    
                    if open_circuits:
                        health_status["warnings"].extend([f"Circuit breaker open: {name}" for name in open_circuits])
                except Exception as e:
                    health_status["components"]["circuit_breaker"] = {
                        "status": "error",
                        "details": f"Circuit breaker error: {str(e)}"
                    }
                
                # Check GPU status if hardware is healthy
                if hardware_health:
                    try:
                        gpus = await self.uow.hardware.get_gpu_info()
                        gpu_alerts = []
                        gpu_warnings = []
                        
                        for gpu in gpus:
                            if gpu.is_overheating:
                                gpu_alerts.append(f"GPU {gpu.id} overheating: {gpu.temperature}°C")
                            elif gpu.temperature > 75:
                                gpu_warnings.append(f"GPU {gpu.id} running warm: {gpu.temperature}°C")
                            
                            if gpu.is_memory_critical:
                                gpu_alerts.append(f"GPU {gpu.id} memory critical: {gpu.memory_usage_percentage:.1f}%")
                            elif gpu.memory_usage_percentage > 80:
                                gpu_warnings.append(f"GPU {gpu.id} memory high: {gpu.memory_usage_percentage:.1f}%")
                        
                        health_status["components"]["gpus"] = {
                            "status": "critical" if gpu_alerts else ("warning" if gpu_warnings else "healthy"),
                            "details": f"{len(gpus)} GPUs detected",
                            "gpu_count": len(gpus)
                        }
                        
                        health_status["alerts"].extend(gpu_alerts)
                        health_status["warnings"].extend(gpu_warnings)
                        
                        if gpu_alerts:
                            health_status["overall_status"] = SystemStatusEnum.CRITICAL.value
                        elif gpu_warnings and health_status["overall_status"] == SystemStatusEnum.HEALTHY.value:
                            health_status["overall_status"] = SystemStatusEnum.WARNING.value
                    
                    except Exception as e:
                        health_status["components"]["gpus"] = {
                            "status": "error",
                            "details": f"GPU monitoring error: {str(e)}"
                        }
                        health_status["warnings"].append("GPU monitoring failed")
                
                # Final status determination
                if health_status["alerts"]:
                    if any("critical" in alert.lower() or "overheating" in alert.lower() 
                          for alert in health_status["alerts"]):
                        health_status["overall_status"] = SystemStatusEnum.CRITICAL.value
                    else:
                        health_status["overall_status"] = SystemStatusEnum.ERROR.value
                elif health_status["warnings"]:
                    health_status["overall_status"] = SystemStatusEnum.WARNING.value
        
        except Exception as e:
            health_status["overall_status"] = SystemStatusEnum.ERROR.value
            health_status["alerts"].append(f"Health check failed: {str(e)}")
            logger.error("Health check failed", error=str(e))
        
        return health_status
    
    async def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information."""
        async with self.uow:
            gpus = await self.uow.hardware.get_gpu_info()
            system_metrics = await self.uow.hardware.get_system_metrics()
            cache_stats = await self.uow.cache.get_stats()
            
            return {
                "system": {
                    "name": "SUPEREZIO Enterprise",
                    "version": "2.0.0",
                    "uptime_seconds": (datetime.utcnow() - self._startup_time).total_seconds(),
                    "startup_time": self._startup_time.isoformat(),
                    "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None
                },
                "hardware": {
                    "gpus": [gpu.model_dump() for gpu in gpus],
                    "gpu_count": len(gpus),
                    "system_metrics": system_metrics
                },
                "cache": cache_stats,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_gpu_status(self) -> Dict[str, Any]:
        """Get detailed GPU status."""
        async with self.uow:
            gpus = await self.uow.hardware.get_gpu_info()
            
            # Analyze GPU health
            alerts = []
            warnings = []
            
            for gpu in gpus:
                if gpu.is_overheating:
                    alerts.append(f"GPU {gpu.id} ({gpu.name}) overheating: {gpu.temperature}°C")
                elif gpu.temperature > 75:
                    warnings.append(f"GPU {gpu.id} ({gpu.name}) running warm: {gpu.temperature}°C")
                
                if gpu.is_memory_critical:
                    alerts.append(f"GPU {gpu.id} ({gpu.name}) memory critical: {gpu.memory_usage_percentage:.1f}%")
                elif gpu.memory_usage_percentage > 80:
                    warnings.append(f"GPU {gpu.id} ({gpu.name}) memory high: {gpu.memory_usage_percentage:.1f}%")
            
            total_memory = sum(gpu.memory_total for gpu in gpus)
            used_memory = sum(gpu.memory_used for gpu in gpus)
            avg_utilization = sum(gpu.gpu_utilization for gpu in gpus) / len(gpus) if gpus else 0
            avg_temperature = sum(gpu.temperature for gpu in gpus) / len(gpus) if gpus else 0
            total_power = sum(gpu.power_draw for gpu in gpus)
            
            # Publish GPU status change event if there are alerts
            if alerts:
                await event_bus.publish(
                    GPUStatusChangedEvent(
                        name="gpu.status_changed",
                        payload={
                            "gpu_count": len(gpus),
                            "alerts": alerts,
                            "warnings": warnings,
                            "avg_temperature": avg_temperature
                        }
                    )
                )
            
            return {
                "gpu_count": len(gpus),
                "gpus": [gpu.model_dump() for gpu in gpus],
                "summary": {
                    "total_memory_mb": total_memory,
                    "used_memory_mb": used_memory,
                    "free_memory_mb": total_memory - used_memory,
                    "memory_usage_percentage": round((used_memory / total_memory * 100), 2) if total_memory > 0 else 0,
                    "average_utilization": round(avg_utilization, 2),
                    "average_temperature": round(avg_temperature, 2),
                    "total_power_draw": round(total_power, 2)
                },
                "alerts": alerts,
                "warnings": warnings,
                "health_status": "critical" if alerts else ("warning" if warnings else "healthy"),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_hardware_monitor(self) -> Dict[str, Any]:
        """Get comprehensive hardware monitoring data."""
        async with self.uow:
            gpus = await self.uow.hardware.get_gpu_info()
            system_metrics = await self.uow.hardware.get_system_metrics()
            hardware_health = await self.uow.hardware.is_healthy()
            
            # Additional monitoring data
            monitoring_data = {
                "hardware_health": hardware_health,
                "monitoring_active": hardware_health,
                "gpus": [gpu.model_dump() for gpu in gpus],
                "system_metrics": system_metrics,
                "timestamp": datetime.utcnow().isoformat(),
                "monitoring_duration": (datetime.utcnow() - self._startup_time).total_seconds()
            }
            
            # Add performance metrics
            if gpus:
                monitoring_data["performance"] = {
                    "peak_temperature": max(gpu.temperature for gpu in gpus),
                    "peak_memory_usage": max(gpu.memory_usage_percentage for gpu in gpus),
                    "peak_utilization": max(gpu.gpu_utilization for gpu in gpus),
                    "total_vram": sum(gpu.memory_total for gpu in gpus),
                    "available_vram": sum(gpu.memory_free for gpu in gpus),
                    "power_efficiency": {
                        "total_power": sum(gpu.power_draw for gpu in gpus),
                        "power_per_utilization": (sum(gpu.power_draw for gpu in gpus) / 
                                                sum(gpu.gpu_utilization for gpu in gpus)) if any(gpu.gpu_utilization for gpu in gpus) else 0
                    }
                }
            
            return monitoring_data
    
    async def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self.uow:
            return await self.uow.cache.get_stats()
    
    async def _reset_system(self) -> Dict[str, Any]:
        """Reset system state."""
        start_time = time.perf_counter()
        
        try:
            async with self.uow:
                # Clear cache
                await self.uow.cache.clear()
                
                # Reset rate limiters
                # Note: This is a simplified reset - in practice you might want more selective resets
                
                # Reset circuit breakers to closed state
                cb_stats = await self.uow.circuit_breaker.get_stats()
                for circuit_name in cb_stats.get("circuit_breakers", {}):
                    await self.uow.circuit_breaker.force_close(circuit_name)
                
                execution_time = (time.perf_counter() - start_time) * 1000
                
                logger.info("System reset completed", execution_time_ms=execution_time)
                
                return {
                    "status": "success",
                    "message": "System reset completed",
                    "actions_performed": [
                        "Cache cleared",
                        "Circuit breakers reset",
                        "System state refreshed"
                    ],
                    "execution_time_ms": execution_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.error("System reset failed", error=str(e), execution_time_ms=execution_time)
            
            return {
                "status": "error",
                "message": f"System reset failed: {str(e)}",
                "execution_time_ms": execution_time,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _handle_custom_command(self, request: CommandRequest) -> Dict[str, Any]:
        """Handle custom commands."""
        command_name = request.parameters.get("command_name", "unknown")
        
        logger.info("Handling custom command",
                   command_name=command_name,
                   parameters=request.parameters)
        
        # Basic custom command handling
        if command_name == "get_detailed_gpu_info":
            return await self._get_detailed_gpu_info(request.parameters)
        elif command_name == "set_gpu_power_limit":
            return await self._set_gpu_power_limit(request.parameters)
        elif command_name == "benchmark_gpu":
            return await self._benchmark_gpu(request.parameters)
        else:
            return {
                "status": "error",
                "message": f"Unknown custom command: {command_name}",
                "available_commands": [
                    "get_detailed_gpu_info",
                    "set_gpu_power_limit", 
                    "benchmark_gpu"
                ]
            }
    
    async def _get_detailed_gpu_info(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information for specific GPU."""
        gpu_id = parameters.get("gpu_id")
        
        async with self.uow:
            gpus = await self.uow.hardware.get_gpu_info()
            
            if gpu_id is None:
                return {"gpus": [gpu.model_dump() for gpu in gpus]}
            
            target_gpu = next((gpu for gpu in gpus if gpu.id == gpu_id), None)
            if not target_gpu:
                return {
                    "status": "error",
                    "message": f"GPU {gpu_id} not found",
                    "available_gpus": [gpu.id for gpu in gpus]
                }
            
            # Enhanced GPU details
            detailed_info = target_gpu.model_dump()
            detailed_info.update({
                "efficiency_metrics": {
                    "power_efficiency": target_gpu.gpu_utilization / target_gpu.power_draw if target_gpu.power_draw > 0 else 0,
                    "memory_efficiency": target_gpu.memory_utilization / target_gpu.memory_usage_percentage if target_gpu.memory_usage_percentage > 0 else 0,
                    "thermal_efficiency": target_gpu.gpu_utilization / target_gpu.temperature if target_gpu.temperature > 0 else 0
                },
                "health_indicators": {
                    "is_overheating": target_gpu.is_overheating,
                    "is_memory_critical": target_gpu.is_memory_critical,
                    "temperature_status": "critical" if target_gpu.temperature > 85 else ("warning" if target_gpu.temperature > 75 else "normal"),
                    "memory_status": "critical" if target_gpu.memory_usage_percentage > 90 else ("warning" if target_gpu.memory_usage_percentage > 80 else "normal")
                }
            })
            
            return {
                "gpu_id": gpu_id,
                "detailed_info": detailed_info,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _set_gpu_power_limit(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Set GPU power limit (simulation - requires NVIDIA ML admin privileges)."""
        gpu_id = parameters.get("gpu_id")
        power_limit = parameters.get("power_limit")
        
        if gpu_id is None or power_limit is None:
            return {
                "status": "error",
                "message": "gpu_id and power_limit parameters required"
            }
        
        # Note: Setting power limits requires admin privileges and proper NVIDIA ML setup
        # This is a simulation for the enterprise system
        
        logger.warning("Power limit change requested (simulation only)",
                      gpu_id=gpu_id,
                      power_limit=power_limit)
        
        return {
            "status": "simulated",
            "message": f"GPU {gpu_id} power limit would be set to {power_limit}W (requires admin privileges)",
            "gpu_id": gpu_id,
            "requested_power_limit": power_limit,
            "note": "This is a simulation - actual power limit changes require administrator privileges"
        }
    
    async def _benchmark_gpu(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Run a simple GPU benchmark."""
        gpu_id = parameters.get("gpu_id")
        duration = parameters.get("duration", 10)  # Default 10 seconds
        
        logger.info("Starting GPU benchmark simulation",
                   gpu_id=gpu_id,
                   duration=duration)
        
        # Simulate benchmark by monitoring GPU for specified duration
        benchmark_data = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            async with self.uow:
                gpus = await self.uow.hardware.get_gpu_info()
                
                if gpu_id is not None:
                    target_gpu = next((gpu for gpu in gpus if gpu.id == gpu_id), None)
                    if target_gpu:
                        benchmark_data.append({
                            "timestamp": time.time(),
                            "utilization": target_gpu.gpu_utilization,
                            "memory_usage": target_gpu.memory_usage_percentage,
                            "temperature": target_gpu.temperature,
                            "power_draw": target_gpu.power_draw
                        })
                else:
                    # Benchmark all GPUs
                    for gpu in gpus:
                        benchmark_data.append({
                            "gpu_id": gpu.id,
                            "timestamp": time.time(),
                            "utilization": gpu.gpu_utilization,
                            "memory_usage": gpu.memory_usage_percentage,
                            "temperature": gpu.temperature,
                            "power_draw": gpu.power_draw
                        })
            
            await asyncio.sleep(1)  # Sample every second
        
        # Calculate benchmark results
        if benchmark_data:
            avg_utilization = sum(d["utilization"] for d in benchmark_data) / len(benchmark_data)
            max_utilization = max(d["utilization"] for d in benchmark_data)
            avg_temperature = sum(d["temperature"] for d in benchmark_data) / len(benchmark_data)
            max_temperature = max(d["temperature"] for d in benchmark_data)
            avg_power = sum(d["power_draw"] for d in benchmark_data) / len(benchmark_data)
            max_power = max(d["power_draw"] for d in benchmark_data)
            
            results = {
                "status": "completed",
                "gpu_id": gpu_id,
                "duration": duration,
                "sample_count": len(benchmark_data),
                "results": {
                    "utilization": {
                        "average": round(avg_utilization, 2),
                        "maximum": round(max_utilization, 2)
                    },
                    "temperature": {
                        "average": round(avg_temperature, 2),
                        "maximum": round(max_temperature, 2)
                    },
                    "power": {
                        "average": round(avg_power, 2),
                        "maximum": round(max_power, 2)
                    }
                },
                "raw_data": benchmark_data[-10:],  # Last 10 samples
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            results = {
                "status": "error",
                "message": "No benchmark data collected",
                "gpu_id": gpu_id,
                "duration": duration
            }
        
        logger.info("GPU benchmark completed",
                   gpu_id=gpu_id,
                   duration=duration,
                   sample_count=len(benchmark_data))
        
        return results
    
    async def get_system_status(self) -> SystemStatus:
        """Get current system status."""
        try:
            async with self.uow:
                gpus = await self.uow.hardware.get_gpu_info()
                system_metrics_dict = await self.uow.hardware.get_system_metrics()
                hardware_health = await self.uow.hardware.is_healthy()
                
                # Convert system metrics dict to SystemMetrics model
                system_metrics = SystemMetrics(
                    cpu_usage=system_metrics_dict["cpu_usage"],
                    memory_usage=system_metrics_dict["memory_usage"],
                    disk_usage=system_metrics_dict["disk_usage"],
                    uptime_seconds=system_metrics_dict["uptime_seconds"],
                    process_count=system_metrics_dict["process_count"]
                )
                
                # Determine overall status
                alerts = []
                status = SystemStatusEnum.HEALTHY
                
                if not hardware_health:
                    alerts.append("Hardware monitoring offline")
                    status = SystemStatusEnum.ERROR
                
                for gpu in gpus:
                    if gpu.is_overheating:
                        alerts.append(f"GPU {gpu.id} overheating")
                        status = SystemStatusEnum.CRITICAL
                    elif gpu.is_memory_critical:
                        alerts.append(f"GPU {gpu.id} memory critical")
                        if status == SystemStatusEnum.HEALTHY:
                            status = SystemStatusEnum.WARNING
                
                # Check system metrics
                if system_metrics.cpu_usage > 90:
                    alerts.append("High CPU usage")
                    if status == SystemStatusEnum.HEALTHY:
                        status = SystemStatusEnum.WARNING
                
                if system_metrics.memory_usage > 90:
                    alerts.append("High memory usage")
                    if status == SystemStatusEnum.HEALTHY:
                        status = SystemStatusEnum.WARNING
                
                services = {
                    "hardware_monitoring": hardware_health,
                    "cache": True,  # Cache is always available
                    "rate_limiter": True,
                    "circuit_breaker": True
                }
                
                return SystemStatus(
                    status=status,
                    timestamp=datetime.utcnow(),
                    gpus=gpus,
                    metrics=system_metrics,
                    services=services,
                    alerts=alerts
                )
        
        except Exception as e:
            logger.error("Failed to get system status", error=str(e))
            
            return SystemStatus(
                status=SystemStatusEnum.ERROR,
                timestamp=datetime.utcnow(),
                gpus=[],
                metrics=None,
                services={},
                alerts=[f"System status check failed: {str(e)}"]
            )
    
    async def shutdown_system(self) -> Dict[str, Any]:
        """Shutdown system gracefully."""
        start_time = time.perf_counter()
        
        logger.info("Starting system shutdown")
        
        try:
            async with self.uow:
                # Shutdown hardware monitoring
                await self.uow.hardware.shutdown()
                
                # Clear cache
                await self.uow.cache.clear()
                
                execution_time = (time.perf_counter() - start_time) * 1000
                
                logger.info("System shutdown completed", execution_time_ms=execution_time)
                
                return {
                    "status": "success",
                    "message": "System shutdown completed",
                    "execution_time_ms": execution_time,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            execution_time = (time.perf_counter() - start_time) * 1000
            logger.error("System shutdown failed", error=str(e), execution_time_ms=execution_time)
            
            return {
                "status": "error",
                "message": f"System shutdown failed: {str(e)}",
                "execution_time_ms": execution_time,
                "timestamp": datetime.utcnow().isoformat()
            }