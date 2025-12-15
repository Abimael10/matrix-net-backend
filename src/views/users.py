from __future__ import annotations

import sqlalchemy
from sqlalchemy import func
from src.db import database, likes_table, post_table, user_table


async def get_profile_with_stats(user_id: int):
    user = await database.fetch_one(user_table.select().where(user_table.c.id == user_id))
    if not user:
        return None

    posts_count_query = (
        sqlalchemy.select(func.count())
        .select_from(post_table)
        .where(post_table.c.user_id == user_id)
    )
    likes_received_query = (
        sqlalchemy.select(func.count())
        .select_from(likes_table.join(post_table, likes_table.c.post_id == post_table.c.id))
        .where(post_table.c.user_id == user_id)
    )
    posts_count = await database.fetch_val(posts_count_query) or 0
    likes_received = await database.fetch_val(likes_received_query) or 0

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "confirmed": user.confirmed,
        "bio": user.bio,
        "location": user.location,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
        "posts_count": posts_count,
        "likes_received": likes_received,
    }
