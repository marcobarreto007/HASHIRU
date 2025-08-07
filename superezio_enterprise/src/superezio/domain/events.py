"""Event system for domain events."""

from typing import List, Callable, Dict, Any, Optional
from abc import ABC, abstractmethod
import asyncio
import weakref
from datetime import datetime
import structlog

from .models import DomainEvent

logger = structlog.get_logger(__name__)


class EventHandler(ABC):
    """Abstract event handler."""
    
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        """Handle a domain event."""
        pass


class EventBus:
    """Event bus for managing domain events."""
    
    def __init__(self):
        self._handlers: Dict[str, List[weakref.ReferenceType]] = {}
        self._middleware: List[Callable] = []
        self._is_processing = False
    
    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Subscribe a handler to an event."""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        
        self._handlers[event_name].append(weakref.ref(handler))
        logger.info("Handler subscribed", event_name=event_name, handler=handler.__class__.__name__)
    
    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from an event."""
        if event_name not in self._handlers:
            return
        
        # Remove dead references and matching handler
        alive_handlers = []
        for handler_ref in self._handlers[event_name]:
            h = handler_ref()
            if h is not None and h != handler:
                alive_handlers.append(handler_ref)
        
        self._handlers[event_name] = alive_handlers
        logger.info("Handler unsubscribed", event_name=event_name, handler=handler.__class__.__name__)
    
    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware to the event bus."""
        self._middleware.append(middleware)
        logger.info("Middleware added", middleware=middleware.__name__)
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribers."""
        if self._is_processing:
            logger.warning("Event bus is already processing, queueing event", event_name=event.name)
            # In a real implementation, you might queue this
            return
        
        self._is_processing = True
        
        try:
            # Apply middleware
            processed_event = event
            for middleware in self._middleware:
                processed_event = await self._apply_middleware(middleware, processed_event)
            
            # Get handlers for this event
            handlers = self._get_alive_handlers(processed_event.name)
            
            if not handlers:
                logger.debug("No handlers for event", event_name=processed_event.name)
                return
            
            # Execute handlers concurrently
            tasks = [self._handle_event(handler, processed_event) for handler in handlers]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info("Event published", 
                       event_name=processed_event.name, 
                       handler_count=len(handlers),
                       correlation_id=processed_event.metadata.correlation_id)
        
        except Exception as e:
            logger.error("Error publishing event", 
                        event_name=event.name, 
                        error=str(e),
                        correlation_id=event.metadata.correlation_id)
        finally:
            self._is_processing = False
    
    async def _apply_middleware(self, middleware: Callable, event: DomainEvent) -> DomainEvent:
        """Apply middleware to an event."""
        try:
            result = middleware(event)
            if asyncio.iscoroutine(result):
                return await result
            return result
        except Exception as e:
            logger.error("Middleware error", middleware=middleware.__name__, error=str(e))
            return event
    
    def _get_alive_handlers(self, event_name: str) -> List[EventHandler]:
        """Get alive handlers for an event, cleaning up dead references."""
        if event_name not in self._handlers:
            return []
        
        alive_handlers = []
        dead_refs = []
        
        for handler_ref in self._handlers[event_name]:
            handler = handler_ref()
            if handler is not None:
                alive_handlers.append(handler)
            else:
                dead_refs.append(handler_ref)
        
        # Clean up dead references
        for dead_ref in dead_refs:
            self._handlers[event_name].remove(dead_ref)
        
        return alive_handlers
    
    async def _handle_event(self, handler: EventHandler, event: DomainEvent) -> None:
        """Handle an event with error handling."""
        try:
            await handler.handle(event)
        except Exception as e:
            logger.error("Event handler error", 
                        handler=handler.__class__.__name__,
                        event_name=event.name,
                        error=str(e),
                        correlation_id=event.metadata.correlation_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        stats = {
            "total_event_types": len(self._handlers),
            "total_handlers": sum(len(handlers) for handlers in self._handlers.values()),
            "middleware_count": len(self._middleware),
            "is_processing": self._is_processing,
            "event_types": {}
        }
        
        for event_name, handlers in self._handlers.items():
            alive_count = len(self._get_alive_handlers(event_name))
            stats["event_types"][event_name] = {
                "handler_count": alive_count,
                "dead_references": len(handlers) - alive_count
            }
        
        return stats


class LoggingEventHandler(EventHandler):
    """Event handler that logs all events."""
    
    async def handle(self, event: DomainEvent) -> None:
        """Log the event."""
        logger.info("Event received",
                   event_name=event.name,
                   payload=event.payload,
                   correlation_id=event.metadata.correlation_id,
                   timestamp=event.metadata.timestamp.isoformat())


class MetricsEventHandler(EventHandler):
    """Event handler that collects metrics."""
    
    def __init__(self):
        self.event_counts: Dict[str, int] = {}
        self.last_event_time: Dict[str, datetime] = {}
    
    async def handle(self, event: DomainEvent) -> None:
        """Collect metrics for the event."""
        event_name = event.name
        
        # Update counters
        self.event_counts[event_name] = self.event_counts.get(event_name, 0) + 1
        self.last_event_time[event_name] = event.metadata.timestamp
        
        logger.debug("Event metrics updated",
                    event_name=event_name,
                    count=self.event_counts[event_name])
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics."""
        return {
            "event_counts": self.event_counts.copy(),
            "last_event_times": {
                name: time.isoformat() 
                for name, time in self.last_event_time.items()
            },
            "total_events": sum(self.event_counts.values())
        }


# Global event bus instance
event_bus = EventBus()

# Register default handlers
logging_handler = LoggingEventHandler()
metrics_handler = MetricsEventHandler()

# Subscribe to all events (using wildcard pattern)
# In a real implementation, you might want more specific subscriptions