from __future__ import annotations

import logging
from typing import Callable, Dict, List, Type, Union
import uuid

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
        message_id = uuid.uuid4()
        logger.debug("message %s received: %s", message_id, message)

        while queue:
            message = queue.pop(0)
            if isinstance(message, events.Event):
                self._handle_event(message, queue, message_id)
            elif isinstance(message, commands.Command):
                result = self._handle_command(message, queue, message_id)
                results.append(result)
            else:
                raise Exception(f"{message} was not an Event or Command")

        return results

    def _handle_event(self, event: events.Event, queue: List[Message], message_id) -> None:
        for handler in self.event_handlers.get(type(event), []):
            try:
                logger.debug("message %s handling event %s with handler %s", message_id, event, handler)
                handler(event)
                queue.extend(self.uow.collect_new_events())
            except Exception:
                logger.exception("message %s exception handling event %s", message_id, event)
                continue

    def _handle_command(self, command: commands.Command, queue: List[Message], message_id):
        logger.debug("message %s handling command %s", message_id, command)
        handler = self.command_handlers.get(type(command))
        if handler is None:
            raise Exception(f"No handler for command type {type(command)}")
        result = handler(command)
        queue.extend(self.uow.collect_new_events())
        return result
