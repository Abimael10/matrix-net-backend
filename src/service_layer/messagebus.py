from __future__ import annotations

import logging
from typing import Callable, Dict, List, Type, Union

from src.domain import commands, events
from src.service_layer import unit_of_work

logger = logging.getLogger(__name__)

Message = Union[commands.Command, events.Event]


class MessageBus:
    def __init__(
        self,
        uow: unit_of_work.AbstractUnitOfWork,
        event_handlers: Dict[Type[events.Event], List[Callable]],
        command_handlers: Dict[Type[commands.Command], Callable],
    ) -> None:
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers

    def handle(self, message: Message) -> List:
        results = []
        queue: List[Message] = [message]

        while queue:
            message = queue.pop(0)
            if isinstance(message, events.Event):
                self._handle_event(message, queue)
            elif isinstance(message, commands.Command):
                result = self._handle_command(message, queue)
                results.append(result)
            else:
                raise Exception(f"{message} was not an Event or Command")

        return results

    def _handle_event(self, event: events.Event, queue: List[Message]) -> None:
        for handler in self.event_handlers.get(type(event), []):
            try:
                logger.debug("handling event %s with handler %s", event, handler)
                handler(event)
                queue.extend(self.uow.collect_new_events())
            except Exception:
                logger.exception("Exception handling event %s", event)
                continue

    def _handle_command(self, command: commands.Command, queue: List[Message]):
        logger.debug("handling command %s", command)
        handler = self.command_handlers.get(type(command))
        if handler is None:
            raise Exception(f"No handler for command type {type(command)}")
        result = handler(command)
        queue.extend(self.uow.collect_new_events())
        return result
