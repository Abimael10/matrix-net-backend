from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db import comment_table, likes_table, post_table, user_table
from src.domain import model
from src.service_layer import repository as abs_repo


class SqlAlchemyUserRepository(abs_repo.AbstractUserRepository):
    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session = session

    def _add(self, user: model.UserAggregate) -> None:
        values = {
            "id": user.user.id,
            "email": user.user.email,
            "username": user.user.username,
            "password": user.password_hash,
            "bio": user.bio,
            "location": user.location,
            "avatar_url": user.avatar_url,
            "confirmed": True,
        }
        stmt = user_table.insert().values(values)
        self.session.execute(stmt)

    def _get(self, user_id: int) -> Optional[model.UserAggregate]:
        stmt = select(user_table).where(user_table.c.id == user_id)
        row = self.session.execute(stmt).mappings().first()
        if not row:
            return None
        return self._row_to_agg(row)

    def _get_by_email(self, email: str) -> Optional[model.UserAggregate]:
        stmt = select(user_table).where(user_table.c.email == email)
        row = self.session.execute(stmt).mappings().first()
        if not row:
            return None
        return self._row_to_agg(row)

    def _get_by_username(self, username: str) -> Optional[model.UserAggregate]:
        stmt = select(user_table).where(user_table.c.username == username)
        row = self.session.execute(stmt).mappings().first()
        if not row:
            return None
        return self._row_to_agg(row)

    def _row_to_agg(self, row) -> model.UserAggregate:
        user_entity = model.User(id=row["id"], email=row["email"], username=row["username"])
        return model.UserAggregate(
            user=user_entity,
            bio=row.get("bio"),
            location=row.get("location"),
            avatar_url=row.get("avatar_url"),
            password_hash=row.get("password"),
        )


class SqlAlchemyPostRepository(abs_repo.AbstractPostRepository):
    def __init__(self, session: Session) -> None:
        super().__init__()
        self.session = session

    def _add(self, post: model.PostAggregate) -> None:
        stmt = post_table.insert().values(
            {
                "id": post.id,
                "user_id": post.user_id,
                "username": post.username,
                "body": post.body,
                "image_url": None,
            }
        )
        self.session.execute(stmt)
        # comments/likes are managed via aggregation behaviors

    def _get(self, post_id: int) -> Optional[model.PostAggregate]:
        stmt = select(post_table).where(post_table.c.id == post_id)
        row = self.session.execute(stmt).mappings().first()
        if not row:
            return None
        return self._hydrate_post(row)

    def _list_by_user(self, user_id: int) -> Iterable[model.PostAggregate]:
        stmt = select(post_table).where(post_table.c.user_id == user_id)
        rows = self.session.execute(stmt).mappings().all()
        return [self._hydrate_post(row) for row in rows]

    def _list_all(self, sort: Optional[str] = None) -> Iterable[model.PostAggregate]:
        stmt = select(post_table)
        rows = self.session.execute(stmt).mappings().all()
        return [self._hydrate_post(row) for row in rows]

    def _hydrate_post(self, row) -> model.PostAggregate:
        post = model.PostAggregate(
            id=row["id"],
            user_id=row["user_id"],
            username=row.get("username", ""),
            body=row["body"],
        )
        # Load comments
        c_stmt = select(comment_table).where(comment_table.c.post_id == post.id)
        for crow in self.session.execute(c_stmt).mappings().all():
            post.comments.add(
                model.Comment(
                    id=crow["id"],
                    post_id=crow["post_id"],
                    user_id=crow["user_id"],
                    body=crow["body"],
                )
            )
        # Load likes
        l_stmt = select(likes_table).where(likes_table.c.post_id == post.id)
        for lrow in self.session.execute(l_stmt).mappings().all():
            post.likes.add(model.Like(post_id=lrow["post_id"], user_id=lrow["user_id"]))
        return post
