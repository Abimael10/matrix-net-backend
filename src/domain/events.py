from dataclasses import dataclass


class Event:
    """Marker base class for domain events."""


@dataclass
class PostCreated(Event):
    post_id: int
    user_id: int
    username: str


@dataclass
class CommentAdded(Event):
    post_id: int
    comment_id: int
    user_id: int


@dataclass
class LikeToggled(Event):
    post_id: int
    user_id: int
    liked: bool


@dataclass
class UserRegistered(Event):
    user_id: int
    email: str
    username: str


@dataclass
class PasswordChanged(Event):
    user_id: int


@dataclass
class FileUploaded(Event):
    file_name: str
    file_url: str
