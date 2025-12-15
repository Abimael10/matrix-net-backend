from __future__ import annotations

import abc
import logging

logger = logging.getLogger(__name__)


class AbstractNotifier(abc.ABC):
    @abc.abstractmethod
    def send(self, to: str, subject: str, body: str) -> None:
        raise NotImplementedError


class LogNotifier(AbstractNotifier):
    def send(self, to: str, subject: str, body: str) -> None:
        logger.info("Notify %s | %s | %s", to, subject, body)


class FakeNotifier(AbstractNotifier):
    def __init__(self):
        self.sent = []

    def send(self, to: str, subject: str, body: str) -> None:
        self.sent.append((to, subject, body))
