from typing import Optional
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_validator


# Posts
class UserPostI(BaseModel):
    body: str


class UserPost(UserPostI):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: str
    image_url: Optional[str] = None
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def ensure_timezone_aware_utc(cls, value):
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromisoformat(str(value))

        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


class UserPostWithLikes(UserPost):
    model_config = ConfigDict(from_attributes=True)

    likes: int


# Comments
class CommentI(BaseModel):
    body: str
    post_id: int


class Comment(CommentI):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    username: Optional[str] = None
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def ensure_timezone_aware_utc(cls, value):
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromisoformat(str(value))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


class UserPostWithComments(BaseModel):
    post: UserPostWithLikes
    comments: list[Comment]


# Likes
class PostLikeI(BaseModel):
    post_id: int


class PostLike(PostLikeI):
    id: int
    user_id: int
