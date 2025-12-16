import pytest

from src import bootstrap
from src.adapters.notifications import FakeNotifier
from src.adapters.storage import FakeFileStorage
from src.domain import commands
from src.service_layer.unit_of_work import FakeUnitOfWork
from src.tests.fakes import FakePostRepository, FakeUserRepository


@pytest.mark.no_db
def test_bootstrap_wires_handlers_with_overrides():
    notifier = FakeNotifier()
    storage = FakeFileStorage()
    uow = FakeUnitOfWork(FakeUserRepository(), FakePostRepository())

    bus = bootstrap.bootstrap(uow=uow, notifier=notifier, file_storage=storage)

    bus.handle(commands.RegisterUser(email="user@example.com", username="user", password="pw"))
    assert notifier.sent[0][0] == "user@example.com"

    result = bus.handle(commands.UploadFile(file_name="pic.png", local_path="/tmp/pic.png"))
    assert result == ["https://fake.local/pic.png"]
    assert storage.uploads[-1][1] == "pic.png"
