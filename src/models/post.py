from typing import Optional

from pydantic import BaseModel, ConfigDict

#POSTS MODEL
class UserPostI(BaseModel):
    body: str

class UserPost(UserPostI):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    image_url: Optional[str] = None

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