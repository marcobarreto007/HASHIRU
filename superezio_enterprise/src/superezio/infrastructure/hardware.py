"""Hardware monitoring implementation."""

import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog
import psutil

from ..domain.models import GPUInfo, SystemMetrics
from ..interfaces.repositories import HardwareRepository

logger = structlog.get_logger(__name__)

try:
    import pynvml
    NVIDIA_ML_AVAILABLE = True
except ImportError:
    NVIDIA_ML_AVAILABLE = False
    logger.warning("pynvml not available, GPU monitoring disabled")


class NVIDIAHardwareRepository(HardwareRepository):
    """NVIDIA GPU hardware repository implementation."""
    
    def __init__(self, polling_interval: float = 5.0):
        self.polling_interval = polling_interval
        self._initialized = False
        self._last_update: Optional[datetime] = None
        self._cached_gpus: List[GPUInfo] = []
        self._cache_valid_duration = timedelta(seconds=2)  # Cache for 2 seconds
        self._lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize NVIDIA ML."""
        if not NVIDIA_ML_AVAILABLE:
            logger.error("NVIDIA ML not available, cannot initialize GPU monitoring")
            raise RuntimeError("pynvml library not available")
        
        try:
            await asyncio.get_event_loop().run_in_executor(None, pynvml.nvmlInit)
            self._initialized = True
            device_count = await asyncio.get_event_loop().run_in_executor(None, pynvml.nvmlDeviceGetCount)
            logger.info("NVIDIA ML initialized", device_count=device_count)
        except Exception as e:
            logger.error("Failed to initialize NVIDIA ML", error=str(e))
            raise
    
    async def shutdown(self) -> None:
        """Shutdown NVIDIA ML."""
        if self._initialized and NVIDIA_ML_AVAILABLE:
            try:
                await asyncio.get_event_loop().run_in_executor(None, pynvml.nvmlShutdown)
                self._initialized = False
                logger.info("NVIDIA ML shutdown completed")
            except Exception as e:
                logger.error("Error during NVIDIA ML shutdown", error=str(e))
    
    async def is_healthy(self) -> bool:
        """Check if GPU monitoring is healthy."""
        if not self._initialized or not NVIDIA_ML_AVAILABLE:
            return False
        
        try:
            # Try to get device count as health check
            await asyncio.get_event_loop().run_in_executor(None, pynvml.nvmlDeviceGetCount)
            return True
        except Exception:
            return False
    
    async def get_gpu_info(self) -> List[GPUInfo]:
        """Get information about all GPUs with caching."""
        async with self._lock:
            # Check cache validity
            if (self._last_update and 
                datetime.utcnow() - self._last_update < self._cache_valid_duration and
                self._cached_gpus):
                logger.debug("Returning cached GPU info")
                return self._cached_gpus.copy()
            
            # Fetch fresh data
            gpus = await self._fetch_gpu_info()
            self._cached_gpus = gpus
            self._last_update = datetime.utcnow()
            return gpus.copy()
    
    async def _fetch_gpu_info(self) -> List[GPUInfo]:
        """Fetch GPU information from NVIDIA ML."""
        if not self._initialized:
            await self.initialize()
        
        gpus = []
        
        try:
            device_count = await asyncio.get_event_loop().run_in_executor(None, pynvml.nvmlDeviceGetCount)
            
            for i in range(device_count):
                try:
                    gpu_info = await self._get_single_gpu_info(i)
                    gpus.append(gpu_info)
                except Exception as e:
                    logger.error("Error getting GPU info", gpu_id=i, error=str(e))
                    # Continue with other GPUs even if one fails
        
        except Exception as e:
            logger.error("Error getting GPU device count", error=str(e))
            raise
        
        logger.debug("Fetched GPU info", gpu_count=len(gpus))
        return gpus
    
    async def _get_single_gpu_info(self, gpu_id: int) -> GPUInfo:
        """Get information for a single GPU."""
        loop = asyncio.get_event_loop()
        
        # Get device handle
        handle = await loop.run_in_executor(None, pynvml.nvmlDeviceGetHandleByIndex, gpu_id)
        
        # Fetch all GPU information in parallel
        tasks = [
            loop.run_in_executor(None, pynvml.nvmlDeviceGetName, handle),
            loop.run_in_executor(None, pynvml.nvmlSystemGetDriverVersion),
            loop.run_in_executor(None, pynvml.nvmlDeviceGetMemoryInfo, handle),
            loop.run_in_executor(None, pynvml.nvmlDeviceGetUtilizationRates, handle),
            loop.run_in_executor(None, pynvml.nvmlDeviceGetTemperature, handle, pynvml.NVML_TEMPERATURE_GPU),
            loop.run_in_executor(None, pynvml.nvmlDeviceGetPowerUsage, handle),
            loop.run_in_executor(None, pynvml.nvmlDeviceGetPowerManagementLimitConstraints, handle),
            loop.run_in_executor(None, pynvml.nvmlDeviceGetClockInfo, handle, pynvml.NVML_CLOCK_GRAPHICS),
            loop.run_in_executor(None, pynvml.nvmlDeviceGetClockInfo, handle, pynvml.NVML_CLOCK_MEM),
        ]
        
        try:
            # Try to get fan speed (may not be available on all GPUs)
            tasks.append(loop.run_in_executor(None, pynvml.nvmlDeviceGetFanSpeed, handle))
            fan_speed_available = True
        except:
            fan_speed_available = False
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extract results
        name = results[0]
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        
        driver_version = results[1]
        if isinstance(driver_version, bytes):
            driver_version = driver_version.decode('utf-8')
        
        memory_info = results[2]
        utilization = results[3]
        temperature = results[4]
        power_usage = results[5] / 1000.0  # Convert to watts
        power_limit_info = results[6]
        graphics_clock = results[7]
        memory_clock = results[8]
        
        fan_speed = None
        if fan_speed_available and len(results) > 9 and not isinstance(results[9], Exception):
            fan_speed = float(results[9])
        
        return GPUInfo(
            id=gpu_id,
            name=name,
            driver_version=driver_version,
            memory_total=memory_info.total // (1024 * 1024),  # Convert to MB
            memory_used=memory_info.used // (1024 * 1024),   # Convert to MB
            memory_free=memory_info.free // (1024 * 1024),   # Convert to MB
            gpu_utilization=float(utilization.gpu),
            memory_utilization=float(utilization.memory),
            temperature=float(temperature),
            power_draw=power_usage,
            power_limit=float(power_limit_info[1]) / 1000.0,  # Max power limit in watts
            clock_graphics=graphics_clock,
            clock_memory=memory_clock,
            fan_speed=fan_speed
        )
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system metrics using psutil."""
        loop = asyncio.get_event_loop()
        
        # Run blocking psutil calls in executor
        cpu_percent = await loop.run_in_executor(None, psutil.cpu_percent, 1.0)
        memory = await loop.run_in_executor(None, psutil.virtual_memory)
        disk = await loop.run_in_executor(None, psutil.disk_usage, '/')
        boot_time = await loop.run_in_executor(None, psutil.boot_time)
        process_count = await loop.run_in_executor(None, len, psutil.pids())
        
        uptime_seconds = int(time.time() - boot_time)
        
        metrics = SystemMetrics(
            cpu_usage=cpu_percent,
            memory_usage=memory.percent,
            disk_usage=disk.percent,
            uptime_seconds=uptime_seconds,
            process_count=process_count
        )
        
        return {
            "cpu_usage": metrics.cpu_usage,
            "memory_usage": metrics.memory_usage,
            "disk_usage": metrics.disk_usage,
            "uptime_seconds": metrics.uptime_seconds,
            "uptime_hours": metrics.uptime_hours,
            "process_count": metrics.process_count,
            "timestamp": datetime.utcnow().isoformat()
        }


class MockHardwareRepository(HardwareRepository):
    """Mock hardware repository for testing or when NVIDIA ML is not available."""
    
    def __init__(self):
        self._initialized = False
        logger.info("Using mock hardware repository")
    
    async def initialize(self) -> None:
        """Initialize mock hardware."""
        self._initialized = True
        logger.info("Mock hardware initialized")
    
    async def shutdown(self) -> None:
        """Shutdown mock hardware."""
        self._initialized = False
        logger.info("Mock hardware shutdown")
    
    async def is_healthy(self) -> bool:
        """Mock is always healthy."""
        return self._initialized
    
    async def get_gpu_info(self) -> List[GPUInfo]:
        """Get mock GPU information."""
        if not self._initialized:
            return []
        
        # Simulate RTX 3060 and RTX 2060
        import random
        
        gpus = [
            GPUInfo(
                id=0,
                name="NVIDIA GeForce RTX 3060",
                driver_version="566.14",
                memory_total=12288,  # 12GB
                memory_used=random.randint(2000, 8000),
                memory_free=0,  # Will be calculated
                gpu_utilization=random.uniform(10, 95),
                memory_utilization=random.uniform(20, 80),
                temperature=random.uniform(45, 80),
                power_draw=random.uniform(100, 170),
                power_limit=170.0,
                clock_graphics=random.randint(1500, 1900),
                clock_memory=random.randint(7000, 8000),
                fan_speed=random.uniform(30, 80)
            ),
            GPUInfo(
                id=1,
                name="NVIDIA GeForce RTX 2060",
                driver_version="566.14",
                memory_total=6144,  # 6GB
                memory_used=random.randint(1000, 4000),
                memory_free=0,  # Will be calculated
                gpu_utilization=random.uniform(5, 90),
                memory_utilization=random.uniform(15, 75),
                temperature=random.uniform(40, 75),
                power_draw=random.uniform(80, 160),
                power_limit=160.0,
                clock_graphics=random.randint(1200, 1700),
                clock_memory=random.randint(6000, 7000),
                fan_speed=random.uniform(25, 75)
            )
        ]
        
        # Calculate free memory
        for gpu in gpus:
            # Create a new instance with calculated free memory
            gpu_dict = gpu.model_dump()
            gpu_dict['memory_free'] = gpu_dict['memory_total'] - gpu_dict['memory_used']
            gpus[gpus.index(gpu)] = GPUInfo(**gpu_dict)
        
        return gpus
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get mock system metrics."""
        import random
        
        metrics = SystemMetrics(
            cpu_usage=random.uniform(10, 60),
            memory_usage=random.uniform(30, 80),
            disk_usage=random.uniform(40, 70),
            uptime_seconds=random.randint(3600, 86400 * 7),  # 1 hour to 7 days
            process_count=random.randint(150, 300)
        )
        
        return {
            "cpu_usage": metrics.cpu_usage,
            "memory_usage": metrics.memory_usage,
            "disk_usage": metrics.disk_usage,
            "uptime_seconds": metrics.uptime_seconds,
            "uptime_hours": metrics.uptime_hours,
            "process_count": metrics.process_count,
            "timestamp": datetime.utcnow().isoformat()
        }