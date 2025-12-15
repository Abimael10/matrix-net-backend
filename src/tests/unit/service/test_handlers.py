import pytest

from src.domain import commands, exceptions, model
from src.service_layer import handlers
from src.tests.fakes import FakeUserRepository, FakePostRepository
from src.service_layer.unit_of_work import FakeUnitOfWork


def make_uow(users=None, posts=None):
    return FakeUnitOfWork(FakeUserRepository(users), FakePostRepository(posts))


def test_register_user_enforces_unique_email():
    existing = model.UserAggregate(user=model.User(id=1, email="a@example.com", username="alice"))
    uow = make_uow(users=[existing])
    cmd = commands.RegisterUser(email="a@example.com", username="bob", password="secret")

    with pytest.raises(exceptions.UserExists):
        handlers.register_user(cmd, uow=uow, hash_password=lambda p: "hashed")


def test_create_post_requires_user():
    uow = make_uow()
    cmd = commands.CreatePost(post_id=None, user_id=99, username="ghost", body="hello")
    with pytest.raises(exceptions.Unauthorized):
        handlers.create_post(cmd, uow=uow)


def test_create_post_succeeds_for_existing_user():
    user = model.UserAggregate(user=model.User(id=1, email="a@example.com", username="alice"))
    uow = make_uow(users=[user])
    cmd = commands.CreatePost(post_id=None, user_id=1, username="alice", body="hello")

    result = handlers.create_post(cmd, uow=uow)
    assert result is not None
    assert uow.posts._posts  # post stored
