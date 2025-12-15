from __future__ import annotations

import sqlalchemy
from sqlalchemy import func
from src.db import comment_table, likes_table, post_table, database


async def list_posts(order: str = "new"):
    base = (
        sqlalchemy.select(
            post_table,
            func.count(likes_table.c.id).label("likes"),
        )
        .select_from(post_table.outerjoin(likes_table))
        .group_by(post_table.c.id)
    )
    if order == "new":
        query = base.order_by(post_table.c.id.desc())
    elif order == "old":
        query = base.order_by(post_table.c.id.asc())
    elif order == "most_likes":
        query = base.order_by(sqlalchemy.desc("likes"))
    else:
        query = base
    return await database.fetch_all(query)


async def get_post_with_comments(post_id: int):
    base = (
        sqlalchemy.select(
            post_table,
            func.count(likes_table.c.id).label("likes"),
        )
        .select_from(post_table.outerjoin(likes_table))
        .where(post_table.c.id == post_id)
        .group_by(post_table.c.id)
    )
    post = await database.fetch_one(base)
    if not post:
        return None
    from src.views.comments import list_comments_for_post

    comments = await list_comments_for_post(post_id)
    return {"post": post, "comments": comments}
