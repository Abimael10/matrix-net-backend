import pytest

from src.domain import commands, events


@pytest.mark.no_db
def test_command_from_dict_ignores_unknown_fields():
    payload = {
        "email": "user@example.com",
        "username": "someone",
        "password": "secret",
        "bio": "ignored-field",
        "unexpected": "drop-me",
    }

    cmd = commands.RegisterUser.from_dict(payload)

    assert cmd.email == "user@example.com"
    assert cmd.username == "someone"
    assert cmd.password == "secret"
    # unknown field should not become an attribute
    assert not hasattr(cmd, "unexpected")


@pytest.mark.no_db
def test_event_from_dict_tolerant_reader():
    payload = {"post_id": 1, "user_id": 2, "username": "alice", "extra": "noise"}

    evt = events.PostCreated.from_dict(payload)

    assert evt.post_id == 1
    assert evt.user_id == 2
    assert evt.username == "alice"
    assert not hasattr(evt, "extra")
