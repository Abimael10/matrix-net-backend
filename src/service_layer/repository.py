from __future__ import annotations

import abc
from typing import Iterable, Optional, Set

from src.domain.model import PostAggregate, UserAggregate


class AbstractUserRepository(abc.ABC):
    def __init__(self) -> None:
        self.seen: Set[UserAggregate] = set()

    def add(self, user: UserAggregate) -> None:
        self._add(user)
        self.seen.add(user)

    def save(self, user: UserAggregate) -> None:
        """Persist mutations on an existing aggregate."""
        self._save(user)
        self.seen.add(user)

    def get(self, user_id: int) -> Optional[UserAggregate]:
        user = self._get(user_id)
        if user:
            self.seen.add(user)
        return user

    def get_by_email(self, email: str) -> Optional[UserAggregate]:
        user = self._get_by_email(email)
        if user:
            self.seen.add(user)
        return user

    def get_by_username(self, username: str) -> Optional[UserAggregate]:
        user = self._get_by_username(username)
        if user:
            self.seen.add(user)
        return user

    @abc.abstractmethod
    def _add(self, user: UserAggregate) -> None: ...

    @abc.abstractmethod
    def _get(self, user_id: int) -> Optional[UserAggregate]: ...

    @abc.abstractmethod
    def _get_by_email(self, email: str) -> Optional[UserAggregate]: ...

    @abc.abstractmethod
    def _get_by_username(self, username: str) -> Optional[UserAggregate]: ...
    
    @abc.abstractmethod
    def _delete(self, user_id: int) -> None: ...

    @abc.abstractmethod
    def _save(self, user: UserAggregate) -> None: ...


class AbstractPostRepository(abc.ABC):
    def __init__(self) -> None:
        self.seen: Set[PostAggregate] = set()

    def add(self, post: PostAggregate) -> None:
        self._add(post)
        self.seen.add(post)

    def get(self, post_id: int) -> Optional[PostAggregate]:
        post = self._get(post_id)
        if post:
            self.seen.add(post)
        return post

    def list_by_user(self, user_id: int) -> Iterable[PostAggregate]:
        posts = list(self._list_by_user(user_id))
        self.seen.update(posts)
        return posts

    def list_all(self, sort: Optional[str] = None) -> Iterable[PostAggregate]:
        posts = list(self._list_all(sort))
        self.seen.update(posts)
        return posts

    @abc.abstractmethod
    def _add(self, post: PostAggregate) -> None: ...

    @abc.abstractmethod
    def _get(self, post_id: int) -> Optional[PostAggregate]: ...

    @abc.abstractmethod
    def _list_by_user(self, user_id: int) -> Iterable[PostAggregate]: ...

    @abc.abstractmethod
    def _list_all(self, sort: Optional[str] = None) -> Iterable[PostAggregate]: ...
