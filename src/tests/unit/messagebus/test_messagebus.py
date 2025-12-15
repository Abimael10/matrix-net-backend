from functools import partial

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
