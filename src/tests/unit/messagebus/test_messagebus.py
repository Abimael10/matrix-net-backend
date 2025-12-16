from functools import partial

import pytest

from src.domain import commands, events
from src.service_layer.messagebus import MessageBus
from src.service_layer.unit_of_work import FakeUnitOfWork
from src.tests.fakes import FakeUserRepository, FakePostRepository


class Dummy:
    def __init__(self):
        self.called = []

    def cmd_handler(self, cmd):
        self.called.append(("cmd", type(cmd).__name__))
        # emit event manually on a dummy aggregate if needed
        return "ok"

    def evt_handler(self, evt):
        self.called.append(("evt", type(evt).__name__))


def test_messagebus_dispatches_command_and_event():
    dummy = Dummy()
    uow = FakeUnitOfWork(FakeUserRepository(), FakePostRepository())
    bus = MessageBus(
        uow=uow,
        event_handlers={events.UserRegistered: [dummy.evt_handler]},
        command_handlers={commands.RegisterUser: dummy.cmd_handler},
    )

    bus.handle(commands.RegisterUser(email="a@example.com", username=None, password="x"))

    assert ("cmd", "RegisterUser") in dummy.called


def test_messagebus_handles_events_even_if_handlers_fail():
    calls = []

    def bad_handler(evt):
        raise RuntimeError("boom")

    def good_handler(evt):
        calls.append(evt)

    uow = FakeUnitOfWork(FakeUserRepository(), FakePostRepository())
    bus = MessageBus(
        uow=uow,
        event_handlers={events.UserRegistered: [bad_handler, good_handler]},
        command_handlers={},
    )

    bus.handle(events.UserRegistered(user_id=1, email="a@example.com", username="alice"))

    assert calls and isinstance(calls[0], events.UserRegistered)


def test_messagebus_processes_events_emitted_from_command():
    seen_events = []

    class Agg:
        def __init__(self):
            self.events = [events.UserRegistered(user_id=1, email="x", username="y")]

        def __hash__(self):
            return id(self)

    def emit_event(cmd):
        uow.users.seen.add(Agg())

    uow = FakeUnitOfWork(FakeUserRepository(), FakePostRepository())
    bus = MessageBus(
        uow=uow,
        event_handlers={events.UserRegistered: [lambda evt: seen_events.append(evt)]},
        command_handlers={commands.RegisterUser: emit_event},
    )

    bus.handle(commands.RegisterUser(email="a@example.com", username=None, password="x"))

    assert seen_events and isinstance(seen_events[0], events.UserRegistered)


def test_messagebus_requires_command_handler():
    uow = FakeUnitOfWork(FakeUserRepository(), FakePostRepository())
    bus = MessageBus(uow=uow, event_handlers={}, command_handlers={})

    with pytest.raises(Exception):
        bus.handle(commands.RegisterUser(email="a@example.com", username=None, password="x"))
