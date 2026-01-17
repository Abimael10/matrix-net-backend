from __future__ import annotations

import sqlalchemy
from sqlalchemy import select
from src.db import comment_table, user_table, database


async def list_comments_for_post(post_id: int):
    # Join with user table to get username for each comment
    query = select(comment_table, user_table.c.username).\
            join(user_table, comment_table.c.user_id == user_table.c.id).\
            where(comment_table.c.post_id == post_id)
    return await database.fetch_all(query)


async def get_comment(comment_id: int):
    # Join with user table to get username for the comment
    query = select(comment_table, user_table.c.username).\
            join(user_table, comment_table.c.user_id == user_table.c.id).\
            where(comment_table.c.id == comment_id)
    return await database.fetch_one(query)
