import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.adapters.repository import SqlAlchemyUserRepository, SqlAlchemyPostRepository
from src.db import metadata, user_table
from src.domain import model


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:", future=True)
    metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        with Session() as sess:
            yield sess
    finally:
        metadata.drop_all(engine)


def test_user_repository_roundtrip(session):
    repo = SqlAlchemyUserRepository(session)
    user_agg = model.UserAggregate(user=model.User(id=None, email="a@example.com", username="alice"))

    repo.add(user_agg)
    session.commit()

    fetched = repo.get_by_email("a@example.com")
    assert fetched is not None
    assert fetched.user.email == "a@example.com"


def test_post_repository_roundtrip(session):
    user_repo = SqlAlchemyUserRepository(session)
    user_agg = model.UserAggregate(user=model.User(id=None, email="a@example.com", username="alice"))
    user_repo.add(user_agg)
    session.commit()
    user_id = session.execute(user_table.select()).mappings().first()["id"]

    repo = SqlAlchemyPostRepository(session)
    post = model.PostAggregate(id=None, user_id=user_id, username="alice", body="hi")
    repo.add(post)
    session.commit()

    fetched = repo.get(post.id)
    assert fetched is not None
    assert fetched.body == "hi"


def test_user_repository_update_and_delete(session):
    repo = SqlAlchemyUserRepository(session)
    user = model.UserAggregate(
        user=model.User(id=None, email="original@example.com", username="orig"),
        bio=None,
        location=None,
        avatar_url=None,
        password_hash="pw",
    )
    repo.add(user)
    session.commit()

    created_id = user.user.id
    fetched = repo.get(created_id)
    assert fetched is not None

    fetched.update_profile(bio="bio", location="earth", avatar_url="http://img")
    fetched.change_password("newpw")
    repo.save(fetched)
    session.commit()

    updated = repo.get_by_username("orig")
    assert updated.bio == "bio"
    assert updated.password_hash == "newpw"

    repo._delete(created_id)
    session.commit()
    assert repo.get(created_id) is None


def test_post_repository_comments_likes_and_listing(session):
    user_repo = SqlAlchemyUserRepository(session)
    user_repo.add(model.UserAggregate(user=model.User(id=None, email="a@example.com", username="alice")))
    user_repo.add(model.UserAggregate(user=model.User(id=None, email="b@example.com", username="bob")))
    session.commit()
    users = session.execute(user_table.select()).mappings().all()
    user_a, user_b = users[0]["id"], users[1]["id"]

    post_repo = SqlAlchemyPostRepository(session)
    post = model.PostAggregate(id=None, user_id=user_a, username="alice", body="hi")
    post_repo.add(post)
    session.commit()

    post.add_comment(comment_id=None, user_id=user_b, body="welcome!")
    post_repo.save(post)
    post_repo.add_like(post.id, user_b)
    session.commit()

    refreshed = post_repo.get(post.id)
    assert refreshed is not None
    assert refreshed.comments  # hydrated comment
    assert any(l.user_id == user_b for l in refreshed.likes)

    post_repo.remove_like(post.id, user_b)
    session.commit()
    refreshed = post_repo.get(post.id)
    assert all(l.user_id != user_b for l in refreshed.likes)

    by_user = list(post_repo.list_by_user(user_a))
    assert by_user and by_user[0].id == post.id

    all_posts = list(post_repo.list_all())
    assert any(p.id == post.id for p in all_posts)
