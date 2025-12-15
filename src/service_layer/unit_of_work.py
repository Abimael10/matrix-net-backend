from __future__ import annotations

import abc
from typing import Iterable, Iterator, List

from sqlalchemy.orm import Session, sessionmaker

from src.db import metadata, SessionLocal
from src.service_layer import repository
from src.adapters import repository as sql_repo


class AbstractUnitOfWork(abc.ABC):
    users: repository.AbstractUserRepository
    posts: repository.AbstractPostRepository

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args) -> None:
        self.rollback()

    def collect_new_events(self) -> List:
        events = []
        for repo in (getattr(self, "users", None), getattr(self, "posts", None)):
            if repo is None:
                continue
            for agg in repo.seen:
                events.extend(getattr(agg, "events", []))
                # clear events after collection
                if hasattr(agg, "events"):
                    agg.events.clear()  # type: ignore[attr-defined]
        return events

    @abc.abstractmethod
    def commit(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    _schema_initialized = False

    def __init__(self, session_factory: sessionmaker | None = None) -> None:
        # Reuse the shared SessionLocal (configured in src.db) by default
        self.session_factory = session_factory or SessionLocal
        self.session: Session | None = None
        self._committed = False

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self.session = self.session_factory()
        self._ensure_schema()
        self.users = sql_repo.SqlAlchemyUserRepository(self.session)
        self.posts = sql_repo.SqlAlchemyPostRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args) -> None:
        super().__exit__(*args)
        if self.session:
            self.session.close()

    def commit(self) -> None:
        if self.session:
            self.session.commit()
            self._committed = True

    def rollback(self) -> None:
        if self.session:
            self.session.rollback()

    def _ensure_schema(self) -> None:
        """
        Guarantee tables exist for the configured database (helpful for SQLite dev/test).
        Runs once per process.
        """
        if self.__class__._schema_initialized:
            return
        if self.session is None:
            return
        metadata.create_all(bind=self.session.bind)
        self.__class__._schema_initialized = True


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        users_repo: repository.AbstractUserRepository,
        posts_repo: repository.AbstractPostRepository,
    ) -> None:
        self.users = users_repo
        self.posts = posts_repo
        self.committed = False

    def __enter__(self) -> "FakeUnitOfWork":
        return super().__enter__()

    def __exit__(self, *args) -> None:
        return super().__exit__(*args)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.committed = False
