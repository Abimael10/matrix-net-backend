from dataclasses import dataclass, fields
from typing import Optional


class Command:
    """Marker base class for commands."""

    @classmethod
    def from_dict(cls, data: dict):
        """
        Tolerant reader: ignore extra fields when constructing commands.
        """
        allowed = {f.name for f in fields(cls) if f.init}
        filtered = {k: v for k, v in data.items() if k in allowed}
        return cls(**filtered)


@dataclass
class RegisterUser(Command):
    email: str
    username: Optional[str]
    password: str
    bio: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None


@dataclass
class LoginUser(Command):
    email: str
    password: str


@dataclass
class CreatePost(Command):
    post_id: Optional[int]
    user_id: int
    username: str
    body: str
    image_url: Optional[str] = None


@dataclass
class AddComment(Command):
    post_id: int
    comment_id: int
    user_id: int
    body: str


@dataclass
class ToggleLike(Command):
    post_id: int
    user_id: int


@dataclass
class UploadFile(Command):
    file_name: str
    local_path: str


@dataclass
class UpdateProfile(Command):
    user_id: int
    bio: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None


@dataclass
class ChangePassword(Command):
    user_id: int
    new_password_hash: str


@dataclass
class DeleteAccount(Command):
    user_id: int
    verify_password_hash: Optional[str] = None
