import logging

import pytest

from src.adapters import notifications, storage


@pytest.mark.no_db
def test_fake_notifier_and_log_notifier(caplog):
    fake = notifications.FakeNotifier()
    fake.send("to@example.com", "Subject", "Body")
    assert fake.sent == [("to@example.com", "Subject", "Body")]

    caplog.set_level(logging.INFO)
    notifier = notifications.LogNotifier()
    notifier.send("to@example.com", "Hi", "Hello there")
    assert any("Notify to@example.com" in message for message in caplog.messages)


@pytest.mark.no_db
def test_file_storage_variants(monkeypatch):
    fake_storage = storage.FakeFileStorage()
    url = fake_storage.upload("/tmp/file.txt", "file.txt")
    assert url.endswith("file.txt")
    assert fake_storage.uploads == [("/tmp/file.txt", "file.txt", url)]

    called = {}

    def fake_upload(local_file: str, file_name: str) -> str:
        called["args"] = (local_file, file_name)
        return "https://b2/files/" + file_name

    monkeypatch.setattr(storage.b2, "b2_upload_file", fake_upload)

    b2_storage = storage.B2FileStorage()
    assert b2_storage.upload("local", "remote.txt") == "https://b2/files/remote.txt"
    assert called["args"] == ("local", "remote.txt")
