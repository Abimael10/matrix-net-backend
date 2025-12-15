from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, Optional, Set

from src.domain.model import PostAggregate, User, UserAggregate
from src.service_layer import repository


class FakeUserRepository(repository.AbstractUserRepository):
    def __init__(self, users: Iterable[UserAggregate] | None = None) -> None:
        super().__init__()
        self._users: Dict[int, UserAggregate] = {}
        if users:
            for u in users:
                self._users[u.user.id] = u

    def _add(self, user: UserAggregate) -> None:
        self._users[user.user.id] = user

    def _get(self, user_id: int) -> Optional[UserAggregate]:
        return self._users.get(user_id)

    def _get_by_email(self, email: str) -> Optional[UserAggregate]:
        return next((u for u in self._users.values() if u.user.email == email), None)

    def _get_by_username(self, username: str) -> Optional[UserAggregate]:
        return next((u for u in self._users.values() if u.user.username == username), None)

    def _delete(self, user_id: int) -> None:
        self._users.pop(user_id, None)


class FakePostRepository(repository.AbstractPostRepository):
    def __init__(self, posts: Iterable[PostAggregate] | None = None) -> None:
        super().__init__()
        self._posts: Dict[int, PostAggregate] = {}
        self._posts_by_user: Dict[int, Set[int]] = defaultdict(set)
        if posts:
            for p in posts:
                self._posts[p.id] = p
                self._posts_by_user[p.user_id].add(p.id)

    def _add(self, post: PostAggregate) -> None:
        self._posts[post.id] = post
        self._posts_by_user[post.user_id].add(post.id)

    def _get(self, post_id: int) -> Optional[PostAggregate]:
        return self._posts.get(post_id)

    def _list_by_user(self, user_id: int) -> Iterable[PostAggregate]:
        ids = self._posts_by_user.get(user_id, set())
        return [self._posts[i] for i in ids]

    def _list_all(self, sort: Optional[str] = None) -> Iterable[PostAggregate]:
        posts = list(self._posts.values())
        # Sorting placeholder: implement by sort key if needed (e.g., created_at)
        return posts
