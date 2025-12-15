from enum import Enum
from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends, Request

from src.domain import commands, exceptions
from src.models.post import (
    UserPostI,
    CommentI,
    PostLikeI,
    UserPostWithLikes,
    UserPostWithComments,
    Comment,
    PostLike,
)
from src.models.user import User
from src.security import get_current_user
from src.views import posts as post_views
from src.views import comments as comment_views

router = APIRouter()

class PostSorting(str, Enum):
    new = "new"
    old = "old"
    most_likes = "most_likes"


def get_bus(request: Request):
    from src.bootstrap import get_message_bus
    return get_message_bus()


@router.post("/api/posts", status_code=201)
async def create_post(
    post: UserPostI,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
):
    bus = get_bus(request)
    cmd = commands.CreatePost(
        post_id=None,
        user_id=current_user.id,
        username=current_user.username,
        body=post.body,
        image_url=None,
    )
    try:
        bus.handle(cmd)
    except exceptions.Unauthorized as e:
        raise HTTPException(status_code=401, detail=str(e))
    return {"detail": "Post created"}


@router.get("/api/posts", response_model=list[UserPostWithLikes], status_code=200)
async def get_all_posts(sorting: PostSorting = PostSorting.new):
    return await post_views.list_posts(order=sorting.value)


@router.post("/api/posts/comment", response_model=Comment, status_code=201)
async def create_comment(
    comment: CommentI,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
):
    bus = get_bus(request)
    cmd = commands.AddComment(
        post_id=comment.post_id,
        comment_id=0,
        user_id=current_user.id,
        body=comment.body,
    )
    try:
        bus.handle(cmd)
    except exceptions.PostNotFound:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"detail": "Comment created"}


@router.get("/api/posts/{post_id}/comment", response_model=list[Comment], status_code=200)
async def get_comments_on_post(post_id: int):
    return await comment_views.list_comments_for_post(post_id)


@router.get("/api/posts/{post_id}", response_model=UserPostWithComments, status_code=200)
async def get_post_with_comments(post_id: int):
    result = await post_views.get_post_with_comments(post_id)
    if not result:
        raise HTTPException(status_code=404, detail="Post not found")
    return result


@router.post("/api/like", response_model=dict, status_code=201)
async def like_post(
    like: PostLikeI,
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
):
    bus = get_bus(request)
    cmd = commands.ToggleLike(post_id=like.post_id, user_id=current_user.id)
    try:
        [liked] = bus.handle(cmd)
    except exceptions.PostNotFound:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"liked": liked}
