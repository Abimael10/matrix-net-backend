import pytest

from src.adapters.notifications import FakeNotifier
from src.domain import commands, events, exceptions, model
from src.domain.model import Like
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


def test_add_comment_persists_and_emits_event():
    user = model.UserAggregate(user=model.User(id=1, email="a@example.com", username="alice"))
    post = model.PostAggregate(id=1, user_id=1, username="alice", body="hello")
    uow = make_uow(users=[user], posts=[post])
    cmd = commands.AddComment(post_id=1, comment_id=0, user_id=2, body="nice!")

    comment_id = handlers.add_comment(cmd, uow=uow)

    assert comment_id is not None
    assert uow.committed is True
    assert uow.posts.last_comment_id == comment_id
    assert any(isinstance(evt, events.CommentAdded) for evt in getattr(post, "events", []))


def test_add_comment_raises_for_missing_post():
    uow = make_uow()
    cmd = commands.AddComment(post_id=999, comment_id=1, user_id=1, body="hello")

    with pytest.raises(exceptions.PostNotFound):
        handlers.add_comment(cmd, uow=uow)


def test_toggle_like_adds_and_removes_likes():
    post = model.PostAggregate(id=1, user_id=1, username="alice", body="hello")
    uow = make_uow(posts=[post])
    cmd = commands.ToggleLike(post_id=1, user_id=2)

    liked = handlers.toggle_like(cmd, uow=uow)
    assert liked is True
    assert Like(post_id=1, user_id=2) in post.likes

    liked = handlers.toggle_like(cmd, uow=uow)
    assert liked is False
    assert Like(post_id=1, user_id=2) not in post.likes


def test_update_profile_and_change_password_emit_events():
    user = model.UserAggregate(user=model.User(id=1, email="a@example.com", username="alice"))
    uow = make_uow(users=[user])

    update_cmd = commands.UpdateProfile(user_id=1, bio="hi", location="earth", avatar_url="img")
    result_id = handlers.update_profile(update_cmd, uow=uow)
    assert result_id == 1
    assert user.bio == "hi"
    assert user.location == "earth"
    assert user.avatar_url == "img"
    assert uow.committed is True

    change_cmd = commands.ChangePassword(user_id=1, new_password_hash="hashed")
    uow.committed = False  # reset flag
    user.events = []

    returned_id = handlers.change_password(change_cmd, uow=uow)

    assert returned_id == 1
    assert user.password_hash == "hashed"
    assert uow.committed is True
    assert any(isinstance(evt, events.PasswordChanged) for evt in user.events)


def test_delete_account_calls_repo_delete():
    user = model.UserAggregate(user=model.User(id=1, email="a@example.com", username="alice"))
    uow = make_uow(users=[user])
    cmd = commands.DeleteAccount(user_id=1)

    deleted_id = handlers.delete_account(cmd, uow=uow)

    assert deleted_id == 1
    assert uow.committed is True
    assert uow.users.get(1) is None


def test_upload_file_uses_storage_and_commits():
    uow = make_uow()
    urls = []
    def fake_storage(path, name):
        url = f"https://files/{name}"
        urls.append((path, name, url))
        return url

    cmd = commands.UploadFile(file_name="pic.png", local_path="/tmp/pic.png")

    url = handlers.upload_file(cmd, uow=uow, file_storage=fake_storage)

    assert url == "https://files/pic.png"
    assert urls == [("/tmp/pic.png", "pic.png", "https://files/pic.png")]
    assert uow.committed is True


def test_event_handlers_execute_without_side_effects():
    uow = make_uow()
    evt = events.FileUploaded(file_name="a.txt", file_url="http://files/a.txt")

    # Should not raise
    handlers.handle_file_uploaded(evt, uow=uow)


def test_handle_user_registered_sends_notification_when_notifier_provided():
    notifier = FakeNotifier()
    evt = events.UserRegistered(user_id=1, email="user@example.com", username="user")

    handlers.handle_user_registered(evt, uow=make_uow(), notifier=notifier)
    assert notifier.sent[0][0] == "user@example.com"

    # Should not raise if notifier is missing
    handlers.handle_user_registered(evt, uow=make_uow(), notifier=None)
