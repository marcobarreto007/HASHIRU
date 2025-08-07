"""Domain models and value objects."""

from typing import Optional, Dict, Any, List, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
from pydantic import BaseModel, Field, ConfigDict
import uuid


class SystemStatusEnum(str, Enum):
    """System status enumeration."""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    OFFLINE = "offline"


class CommandTypeEnum(str, Enum):
    """Command type enumeration."""
    SYSTEM_INFO = "system_info"
    GPU_STATUS = "gpu_status"
    HARDWARE_MONITOR = "hardware_monitor"
    CACHE_STATS = "cache_stats"
    HEALTH_CHECK = "health_check"
    RESET_SYSTEM = "reset_system"
    CUSTOM = "custom"


class GPUInfo(BaseModel):
    """GPU information model."""
    
    model_config = ConfigDict(frozen=True)
    
    id: int = Field(..., description="GPU ID")
    name: str = Field(..., description="GPU name")
    driver_version: str = Field(..., description="Driver version")
    memory_total: int = Field(..., description="Total memory in MB")
    memory_used: int = Field(..., description="Used memory in MB")
    memory_free: int = Field(..., description="Free memory in MB")
    gpu_utilization: float = Field(..., ge=0, le=100, description="GPU utilization percentage")
    memory_utilization: float = Field(..., ge=0, le=100, description="Memory utilization percentage")
    temperature: float = Field(..., description="Temperature in Celsius")
    power_draw: float = Field(..., description="Power draw in watts")
    power_limit: float = Field(..., description="Power limit in watts")
    clock_graphics: int = Field(..., description="Graphics clock in MHz")
    clock_memory: int = Field(..., description="Memory clock in MHz")
    fan_speed: Optional[float] = Field(None, description="Fan speed percentage")
    
    @property
    def memory_usage_percentage(self) -> float:
        """Calculate memory usage percentage."""
        if self.memory_total == 0:
            return 0.0
        return (self.memory_used / self.memory_total) * 100
    
    @property
    def is_overheating(self) -> bool:
        """Check if GPU is overheating (above 85°C)."""
        return self.temperature >= 85.0
    
    @property
    def is_memory_critical(self) -> bool:
        """Check if memory usage is critical (above 90%)."""
        return self.memory_usage_percentage >= 90.0


class SystemMetrics(BaseModel):
    """System metrics model."""
    
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    memory_usage: float = Field(..., ge=0, le=100, description="Memory usage percentage")
    disk_usage: float = Field(..., ge=0, le=100, description="Disk usage percentage")
    uptime_seconds: int = Field(..., ge=0, description="System uptime in seconds")
    process_count: int = Field(..., ge=0, description="Number of processes")
    
    @property
    def uptime_hours(self) -> float:
        """Get uptime in hours."""
        return self.uptime_seconds / 3600


class SystemStatus(BaseModel):
    """System status model."""
    
    model_config = ConfigDict(frozen=True)
    
    status: SystemStatusEnum = Field(..., description="Overall system status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status timestamp")
    gpus: List[GPUInfo] = Field(default_factory=list, description="GPU information")
    metrics: Optional[SystemMetrics] = Field(None, description="System metrics")
    services: Dict[str, bool] = Field(default_factory=dict, description="Service status")
    alerts: List[str] = Field(default_factory=list, description="Active alerts")
    
    @property
    def has_critical_alerts(self) -> bool:
        """Check if there are critical alerts."""
        return self.status in [SystemStatusEnum.ERROR, SystemStatusEnum.CRITICAL]
    
    @property
    def gpu_count(self) -> int:
        """Get number of GPUs."""
        return len(self.gpus)
    
    @property
    def total_gpu_memory(self) -> int:
        """Get total GPU memory across all GPUs."""
        return sum(gpu.memory_total for gpu in self.gpus)


class CommandRequest(BaseModel):
    """Command request model."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Request ID")
    command_type: CommandTypeEnum = Field(..., description="Command type")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Command parameters")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Request timestamp")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CommandResponse(BaseModel):
    """Command response model."""
    
    request_id: str = Field(..., description="Original request ID")
    success: bool = Field(..., description="Success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    message: str = Field(default="", description="Response message")
    error_code: Optional[str] = Field(None, description="Error code if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    execution_time_ms: float = Field(..., description="Execution time in milliseconds")
    
    @property
    def is_error(self) -> bool:
        """Check if response is an error."""
        return not self.success or self.error_code is not None


@dataclass(frozen=True)
class EventMetadata:
    """Event metadata value object."""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = "superezio"
    version: str = "2.0.0"


@dataclass(frozen=True)
class DomainEvent:
    """Base domain event."""
    name: str
    payload: Dict[str, Any]
    metadata: EventMetadata = field(default_factory=EventMetadata)


# Specific domain events
@dataclass(frozen=True)
class SystemStartedEvent(DomainEvent):
    """System started event."""
    def __post_init__(self):
        object.__setattr__(self, 'name', 'system.started')


@dataclass(frozen=True)
class GPUStatusChangedEvent(DomainEvent):
    """GPU status changed event."""
    def __post_init__(self):
        object.__setattr__(self, 'name', 'gpu.status_changed')


@dataclass(frozen=True)
class CommandExecutedEvent(DomainEvent):
    """Command executed event."""
    def __post_init__(self):
        object.__setattr__(self, 'name', 'command.executed')


@dataclass(frozen=True)
class SystemErrorEvent(DomainEvent):
    """System error event."""
    def __post_init__(self):
        object.__setattr__(self, 'name', 'system.error')