from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Set


# --- Value objects (kept simple/primitive-friendly for now) ---


# --- Entities ---


@dataclass(eq=True, frozen=True)
class User:
    id: int
    email: str
    username: str


@dataclass(eq=True, frozen=True)
class Comment:
    id: int
    post_id: int
    user_id: int
    body: str


@dataclass(eq=True, frozen=True)
class Like:
    post_id: int
    user_id: int


# --- Aggregates ---


@dataclass
class UserAggregate:
    user: User
    bio: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None
    password_hash: Optional[str] = None

    def update_profile(
        self,
        bio: Optional[str] = None,
        location: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> None:
        if bio is not None:
            self.bio = bio
        if location is not None:
            self.location = location
        if avatar_url is not None:
            self.avatar_url = avatar_url

    def change_password(self, new_password_hash: str) -> None:
        if not new_password_hash:
            from src.domain import exceptions

            raise exceptions.InvalidOperation("Password hash cannot be empty")
        self.password_hash = new_password_hash


@dataclass
class PostAggregate:
    id: int | None
    user_id: int
    username: str
    body: str
    comments: Set[Comment] = field(default_factory=set)
    likes: Set[Like] = field(default_factory=set)

    def add_comment(self, comment_id: int, user_id: int, body: str) -> Comment:
        if not body:
            from src.domain import exceptions

            raise exceptions.InvalidOperation("Comment body cannot be empty")
        comment = Comment(id=comment_id, post_id=self.id, user_id=user_id, body=body)
        self.comments.add(comment)
        return comment

    def toggle_like(self, user_id: int) -> Like | None:
        like = Like(post_id=self.id, user_id=user_id)
        if like in self.likes:
            self.likes.remove(like)
            return None
        self.likes.add(like)
        return like
