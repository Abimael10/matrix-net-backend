from dataclasses import dataclass, fields


class Event:
    """Marker base class for domain events."""

    @classmethod
    def from_dict(cls, data: dict):
        """
        Tolerant reader for inbound events: ignore unknown fields.
        """
        allowed = {f.name for f in fields(cls) if f.init}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)


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
