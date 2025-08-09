from enum import Enum
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends
from src.db import comment_table, likes_table, post_table, database

import sqlalchemy

from src.models.post import (
    UserPostI, 
    UserPost, 
    Comment, 
    CommentI, 
    PostLikeI,
    PostLike,
    UserPostWithComments,
    UserPostWithLikes
)
from src.models.user import User
from src.security import get_current_user

router = APIRouter()

#Query to select post with its amount of likes basically
#Will see about optimizing the way I query like this since
#it gets closer to SQL-like without doing too much magic with these ORMs...
select_post_and_likes = (
    sqlalchemy.select(post_table, sqlalchemy.func.count(likes_table.c.id).label("likes"))
    .select_from(post_table.outerjoin(likes_table))
    .group_by(post_table.c.id)
)

async def find_post(post_id: int):
    query = post_table.select().where(post_table.c.id == post_id)
    return await database.fetch_one(query)

#POST create a post
@router.post("/api/posts", response_model=UserPost, status_code=201)
async def create_post(
    post: UserPostI, 
    current_user: Annotated[User, Depends(get_current_user)]
):

    data = {
        **post.model_dump(),
        "user_id": current_user.id,
        "username": current_user.username,
    }
    query = post_table.insert().values(data)
    last_record_id = await database.execute(query)
    # Fetch the inserted row to include server defaults like created_at
    created = await database.fetch_one(
        post_table.select().where(post_table.c.id == last_record_id)
    )
    return created

#Helper enum for post sorting
class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"

#GET all the posts
@router.get("/api/posts", response_model=list[UserPostWithLikes], status_code=200)
async def get_all_posts(sorting: PostSorting = PostSorting.new):

    if sorting == PostSorting.new:
        query = select_post_and_likes.order_by(post_table.c.id.desc())
    elif sorting == PostSorting.old:
        query = select_post_and_likes.order_by(post_table.c.id.asc())
    elif sorting == PostSorting.most_likes:
        query = select_post_and_likes.order_by(sqlalchemy.desc("likes"))

    return await database.fetch_all(query)

#POST create a comment a post
@router.post("/api/posts/comment", response_model=Comment, status_code=201)
async def create_comment(
    comment: CommentI, 
    current_user: Annotated[User, Depends(get_current_user)]
):

    post = await find_post(comment.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    data = {**comment.model_dump(), "user_id": current_user.id}
    query = comment_table.insert().values(data)
    last_record_id = await database.execute(query)

    return {**data, "id": last_record_id, }

#GET a single post comments
@router.get("/api/posts/{post_id}/comment", response_model=list[Comment], status_code=200)
async def get_comments_on_post(post_id: int):
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    return await database.fetch_all(query)

#GET a single post and all its comments
@router.get("/api/posts/{post_id}", response_model=UserPostWithComments, status_code=200)
async def get_post_with_comments(post_id: int):

    query = select_post_and_likes.where(post_table.c.id == post_id)

    post = await database.fetch_one(query)

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {
        "post": post, 
        "comments": await get_comments_on_post(post_id),
    }

@router.post("/api/like", response_model=PostLike, status_code=201)
async def like_post(
    like: PostLikeI, 
    current_user: Annotated[User, Depends(get_current_user)]
):
    
    post = await find_post(like.post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    data = {**like.model_dump(), "user_id": current_user.id}
    query = likes_table.insert().values(data)
    
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}