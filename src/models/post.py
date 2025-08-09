from typing import Optional
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_validator

#POSTS MODEL
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
            # Pydantic may pass a string from DB; parse to datetime
            dt = datetime.fromisoformat(str(value))

        if dt.tzinfo is None:
            # Assume DB timestamps are in UTC when tzinfo is missing
            return dt.replace(tzinfo=timezone.utc)
        # Normalize to UTC
        return dt.astimezone(timezone.utc)

class UserPostWithLikes(UserPost):
    model_config = ConfigDict(from_attributes=True)

    likes: int

#COMMENTS TO POSTS MODEL
class CommentI(BaseModel):
    body: str
    post_id: int

class Comment(CommentI):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int

class UserPostWithComments(BaseModel):
    post: UserPostWithLikes
    comments: list[Comment]

#LIKES OF A USER TO POSTS MODEL

class PostLikeI(BaseModel):
    post_id: int

class PostLike(PostLikeI):
    id: int
    user_id: int