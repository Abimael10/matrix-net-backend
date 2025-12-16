import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db import metadata
from src.domain import events, model
from src.service_layer.unit_of_work import FakeUnitOfWork, SqlAlchemyUnitOfWork
from src.tests.fakes import FakePostRepository, FakeUserRepository


@pytest.mark.no_db
def test_collect_new_events_clears_event_queues():
    user = model.UserAggregate(user=model.User(id=1, email="a@example.com", username="alice"))
    user.events = [events.UserRegistered(user_id=1, email="a@example.com", username="alice")]  # type: ignore[attr-defined]
    post = model.PostAggregate(id=1, user_id=1, username="alice", body="hi")
    post.events = [events.PostCreated(post_id=1, user_id=1, username="alice")]  # type: ignore[attr-defined]

    uow = FakeUnitOfWork(FakeUserRepository([user]), FakePostRepository([post]))
    uow.users.seen.add(user)
    uow.posts.seen.add(post)

    collected = uow.collect_new_events()

    assert collected == [
        events.UserRegistered(user_id=1, email="a@example.com", username="alice"),
        events.PostCreated(post_id=1, user_id=1, username="alice"),
    ]
    assert getattr(user, "events") == []
    assert getattr(post, "events") == []


def _make_session_factory():
    engine = create_engine("sqlite:///:memory:")
    metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


def test_sqlalchemy_uow_commit_and_rollback():
    session_factory = _make_session_factory()
    SqlAlchemyUnitOfWork._schema_initialized = False

    with SqlAlchemyUnitOfWork(session_factory=session_factory) as uow:
        uow.users.add(model.UserAggregate(user=model.User(id=None, email="a@example.com", username="alice")))
        uow.commit()
        user_id = uow.users.get_by_email("a@example.com").user.id  # type: ignore[union-attr]

    with SqlAlchemyUnitOfWork(session_factory=session_factory) as uow:
        assert uow.users.get(user_id) is not None
        uow.users.add(model.UserAggregate(user=model.User(id=None, email="b@example.com", username="bob")))
        uow.rollback()

    with SqlAlchemyUnitOfWork(session_factory=session_factory) as uow:
        assert uow.users.get_by_email("b@example.com") is None


@pytest.mark.no_db
def test_ensure_schema_runs_only_once(monkeypatch):
    session_factory = _make_session_factory()
    SqlAlchemyUnitOfWork._schema_initialized = False
    calls = []

    original = metadata.create_all

    def wrapper(bind):
        calls.append(bind)
        return original(bind)

    monkeypatch.setattr(metadata, "create_all", wrapper)

    with SqlAlchemyUnitOfWork(session_factory=session_factory):
        pass
    with SqlAlchemyUnitOfWork(session_factory=session_factory):
        pass

    assert len(calls) == 1
