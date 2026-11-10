"""
Event publisher and asynchronous message broker integrations.

Provides event bus abstractions and an in-memory event bus implementation
for event-driven synchronization and background worker tasks.
"""
import asyncio
from collections import defaultdict
from typing import Any, Callable, Coroutine

import structlog

logger = structlog.get_logger(__name__)

EventHandler = Callable[[Any], Coroutine[Any, Any, None]]


class InMemoryEventBus:
    """
    In-memory asynchronous event bus supporting typed pub/sub event distribution.

    Used within application services and background workers to publish and handle
    domain events without tight coupling.
    """

    def __init__(self) -> None:
        self._handlers: dict[type, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """
        Subscribe an asynchronous handler to an event class.

        Args:
            event_type: Type/class of the domain event.
            handler: Async callable taking the event instance.
        """
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(
                "Subscribed event handler",
                event_type=event_type.__name__,
                handler=getattr(handler, "__name__", str(handler)),
            )

    def unsubscribe(self, event_type: type, handler: EventHandler) -> None:
        """
        Unsubscribe an asynchronous handler from an event class.

        Args:
            event_type: Type/class of the domain event.
            handler: Async callable to remove.
        """
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def publish(self, event: Any) -> None:
        """
        Publish an event concurrently to all registered handlers.

        Args:
            event: Domain event instance.
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            logger.debug("No handlers for event", event_type=event_type.__name__)
            return

        tasks = [asyncio.create_task(handler(event)) for handler in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res, handler in zip(results, handlers):
            if isinstance(res, Exception):
                logger.error(
                    "Event handler failed",
                    event_type=event_type.__name__,
                    handler=getattr(handler, "__name__", str(handler)),
                    error=str(res),
                )
