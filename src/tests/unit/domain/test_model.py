import pytest

from src.domain import exceptions
from src.domain.model import Comment, Like, PostAggregate, User, UserAggregate

# Pure unit tests: skip DB autouse fixture, allow async fixture plumbing via anyio
pytestmark = [pytest.mark.no_db, pytest.mark.anyio]


def test_post_adds_comment_and_returns_comment():
    post = PostAggregate(id=1, user_id=2, username="alice", body="hello world")

    comment = post.add_comment(comment_id=10, user_id=3, body="nice post")

    assert comment in post.comments
    assert isinstance(comment, Comment)
    assert comment.post_id == post.id


def test_post_rejects_empty_comment():
    post = PostAggregate(id=1, user_id=2, username="alice", body="hello world")

    with pytest.raises(exceptions.InvalidOperation):
        post.add_comment(comment_id=11, user_id=3, body="")


def test_post_toggle_like_adds_and_removes():
    post = PostAggregate(id=1, user_id=2, username="alice", body="hello world")

    like = post.toggle_like(user_id=3)
    assert like == Like(post_id=1, user_id=3)
    assert like in post.likes

    removed = post.toggle_like(user_id=3)
    assert removed is None
    assert Like(post_id=1, user_id=3) not in post.likes


def test_user_profile_updates_and_password_change():
    agg = UserAggregate(user=User(id=1, email="a@example.com", username="alice"))

    agg.update_profile(bio="hi", location="earth", avatar_url="http://img")
    assert agg.bio == "hi"
    assert agg.location == "earth"
    assert agg.avatar_url == "http://img"

    agg.change_password("hashed")
    assert agg.password_hash == "hashed"

    with pytest.raises(exceptions.InvalidOperation):
        agg.change_password("")
