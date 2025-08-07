"""Structured logging setup using structlog."""

import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Any, Optional
import structlog
from rich.console import Console
from rich.logging import RichHandler

from config.settings import LoggingConfig


def setup_logging(config: LoggingConfig) -> None:
    """Setup structured logging with rich console output."""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.level.upper(), logging.INFO),
    )
    
    # Configure processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.processors.CallsiteParameterAdder(
            parameters=[structlog.processors.CallsiteParameter.FILENAME,
                       structlog.processors.CallsiteParameter.FUNC_NAME,
                       structlog.processors.CallsiteParameter.LINENO]
        ),
    ]
    
    # Configure output format
    if config.format.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, config.level.upper(), logging.INFO)
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Setup file logging if configured
    if config.file_path:
        setup_file_logging(config)
    
    # Setup rich console logging for development
    if config.format.lower() != "json":
        setup_rich_logging(config)
    
    logger = structlog.get_logger(__name__)
    logger.info("Logging configured",
               level=config.level,
               format=config.format,
               file_path=str(config.file_path) if config.file_path else None)


def setup_file_logging(config: LoggingConfig) -> None:
    """Setup file logging with rotation."""
    if not config.file_path:
        return
    
    # Ensure log directory exists
    log_path = Path(config.file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Setup rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_path,
        maxBytes=config.max_size,
        backupCount=config.backup_count,
        encoding='utf-8'
    )
    
    # Configure formatter
    if config.format.lower() == "json":
        formatter = logging.Formatter('%(message)s')
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    
    # Add to root logger
    logging.getLogger().addHandler(file_handler)


def setup_rich_logging(config: LoggingConfig) -> None:
    """Setup rich console logging for beautiful output."""
    console = Console(force_terminal=True)
    
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_level=True,
        show_path=True,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=True
    )
    
    rich_handler.setLevel(getattr(logging, config.level.upper(), logging.INFO))
    
    # Replace default handlers with rich handler
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
            root_logger.removeHandler(handler)
    
    root_logger.addHandler(rich_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin to add logging capabilities to classes."""
    
    @property
    def logger(self) -> structlog.BoundLogger:
        """Get logger for this class."""
        return structlog.get_logger(self.__class__.__name__)


def log_async_exceptions(logger: structlog.BoundLogger):
    """Decorator to log async exceptions."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error("Async function failed",
                           function=func.__name__,
                           error=str(e),
                           error_type=type(e).__name__)
                raise
        return wrapper
    return decorator


def log_execution_time(logger: structlog.BoundLogger):
    """Decorator to log function execution time."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            import time
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time
                logger.debug("Function completed",
                           function=func.__name__,
                           execution_time_ms=round(execution_time * 1000, 2))
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                logger.error("Function failed",
                           function=func.__name__,
                           execution_time_ms=round(execution_time * 1000, 2),
                           error=str(e))
                raise
        
        def sync_wrapper(*args, **kwargs):
            import time
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                execution_time = time.perf_counter() - start_time
                logger.debug("Function completed",
                           function=func.__name__,
                           execution_time_ms=round(execution_time * 1000, 2))
                return result
            except Exception as e:
                execution_time = time.perf_counter() - start_time
                logger.error("Function failed",
                           function=func.__name__,
                           execution_time_ms=round(execution_time * 1000, 2),
                           error=str(e))
                raise
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class StructuredLogger:
    """Enhanced structured logger with context management."""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = structlog.get_logger(name)
        self._context: Dict[str, Any] = {}
    
    def bind(self, **kwargs) -> 'StructuredLogger':
        """Bind context to logger."""
        new_logger = StructuredLogger(self.name)
        new_logger._context = {**self._context, **kwargs}
        new_logger.logger = self.logger.bind(**new_logger._context)
        return new_logger
    
    def debug(self, msg: str, **kwargs):
        """Log debug message."""
        self.logger.debug(msg, **kwargs)
    
    def info(self, msg: str, **kwargs):
        """Log info message."""
        self.logger.info(msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        """Log warning message."""
        self.logger.warning(msg, **kwargs)
    
    def error(self, msg: str, **kwargs):
        """Log error message."""
        self.logger.error(msg, **kwargs)
    
    def critical(self, msg: str, **kwargs):
        """Log critical message."""
        self.logger.critical(msg, **kwargs)
    
    def exception(self, msg: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(msg, **kwargs)


# Utility functions for common logging patterns
def log_system_event(event_type: str, **details):
    """Log system events with consistent structure."""
    logger = structlog.get_logger("system")
    logger.info("System event",
               event_type=event_type,
               timestamp=structlog.processors.TimeStamper(fmt="ISO")(),
               **details)


def log_performance(operation: str, duration_ms: float, **context):
    """Log performance metrics."""
    logger = structlog.get_logger("performance")
    logger.info("Performance metric",
               operation=operation,
               duration_ms=duration_ms,
               **context)


def log_security_event(event_type: str, severity: str = "INFO", **details):
    """Log security-related events."""
    logger = structlog.get_logger("security")
    logger.log(getattr(logging, severity.upper(), logging.INFO),
              "Security event",
              event_type=event_type,
              severity=severity,
              **details)


# Context managers for structured logging
class LogContext:
    """Context manager for adding context to all logs within a block."""
    
    def __init__(self, **context):
        self.context = context
        self.token = None
    
    def __enter__(self):
        self.token = structlog.contextvars.bind_contextvars(**self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            structlog.contextvars.unbind_contextvars(self.token)


def with_log_context(**context):
    """Decorator to add context to all logs within a function."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            with LogContext(**context):
                return await func(*args, **kwargs)
        
        def sync_wrapper(*args, **kwargs):
            with LogContext(**context):
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator