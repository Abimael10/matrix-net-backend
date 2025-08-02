from pydantic import BaseModel, ConfigDict

#POSTS MODEL
class UserPostI(BaseModel):
    body: str

class UserPost(UserPostI):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int

#COMMENTS TO POSTS MODEL
class CommentI(BaseModel):
    body: str
    post_id: int

class Comment(CommentI):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int

class UserPostWithComments(BaseModel):
    post: UserPost
    comments: list[Comment]