"""
SUPEREZIO Enterprise Edition
Modern AI Cognitive System with Hardware Management
"""

__version__ = "2.0.0"
__author__ = "Marco Barreto"
__description__ = "Enterprise AI System with GPU Management"

from .domain.models import SystemStatus, GPUInfo, CommandRequest, CommandResponse
from .application.use_cases import SystemUseCase
from .config.container import Container

__all__ = [
    "SystemStatus",
    "GPUInfo", 
    "CommandRequest",
    "CommandResponse",
    "SystemUseCase",
    "Container"
]