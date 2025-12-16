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
            # id may be None => autoincrement
            "email": user.user.email,
            "username": user.user.username,
            "password": user.password_hash,
            "bio": user.bio,
            "location": user.location,
            "avatar_url": user.avatar_url,
            "confirmed": True,
        }
        stmt = user_table.insert().values(values).returning(user_table.c.id)
        result = self.session.execute(stmt).scalar_one()
        # update aggregate id if needed
        user.user = model.User(id=result, email=user.user.email, username=user.user.username)

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

    def _delete(self, user_id: int) -> None:
        self.session.execute(user_table.delete().where(user_table.c.id == user_id))

    def _save(self, user: model.UserAggregate) -> None:
        """Persist in-memory changes to the users table."""
        self.session.execute(
            user_table.update()
            .where(user_table.c.id == user.user.id)
            .values(
                bio=user.bio,
                location=user.location,
                avatar_url=user.avatar_url,
                password=user.password_hash,
            )
        )

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
        self._last_comment_id = None

    def _add(self, post: model.PostAggregate) -> None:
        values = {
            "user_id": post.user_id,
            "username": post.username,
            "body": post.body,
            "image_url": None,
        }
        if post.id is not None:
            values["id"] = post.id
        stmt = post_table.insert().values(values).returning(post_table.c.id)
        new_id = self.session.execute(stmt).scalar_one()
        post.id = new_id

    def _save(self, post: model.PostAggregate) -> None:
        # Persist new comments/likes embedded in the aggregate
        if post.id is None:
            self._add(post)
            return
        # Save new comments
        for comment in list(post.comments):
            # comment.id None or 0 => new
            if getattr(comment, "id", None) in (None, 0):
                stmt = comment_table.insert().values(
                    post_id=post.id,
                    user_id=comment.user_id,
                    body=comment.body,
                    username=None,
                ).returning(comment_table.c.id)
                new_id = self.session.execute(stmt).scalar_one()
                self.last_comment_id = new_id
                # replace with a new Comment carrying the db id
                post.comments.remove(comment)
                post.comments.add(
                    model.Comment(
                        id=new_id,
                        post_id=post.id,
                        user_id=comment.user_id,
                        body=comment.body,
                    )
                )
        # Likes are handled via explicit add/remove methods

    def _add_like(self, post_id: int, user_id: int) -> None:
        self.session.execute(
            likes_table.insert().values(post_id=post_id, user_id=user_id)
        )

    def _remove_like(self, post_id: int, user_id: int) -> None:
        self.session.execute(
            likes_table.delete().where(
                likes_table.c.post_id == post_id, likes_table.c.user_id == user_id
            )
        )
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
