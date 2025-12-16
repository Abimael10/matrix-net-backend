from __future__ import annotations

import sqlalchemy
from src.db import comment_table, database


async def list_comments_for_post(post_id: int):
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    return await database.fetch_all(query)


async def get_comment(comment_id: int):
    query = comment_table.select().where(comment_table.c.id == comment_id)
    return await database.fetch_one(query)
