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
    with Session() as sess:
        yield sess
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
