from typing import Optional, ClassVar
from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr, field_validator
import re

class User(BaseModel):
    id: int | None = None
    username: str
    email: EmailStr
    bio: str | None = None
    location: str | None = None
    avatar_url: str | None = None
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

class UserI(User):
    password : str

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    username: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    avatar_url: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# Profile update input with sanitization
class UserProfileUpdate(BaseModel):
    bio: Optional[str] = None
    location: Optional[str] = None

    MAX_BIO_LENGTH: ClassVar[int] = 500
    MAX_LOCATION_LENGTH: ClassVar[int] = 100

    @staticmethod
    def _sanitize_text(value: Optional[str], max_length: int) -> Optional[str]:
        if value is None:
            return None
        text = value.strip()
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Normalize internal whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove non-printable control characters (preserve tabs/newlines already normalized)
        text = "".join(ch for ch in text if ch.isprintable())
        if not text:
            return None
        if len(text) > max_length:
            text = text[:max_length]
        return text

    @field_validator("bio", mode="before")
    @classmethod
    def sanitize_bio(cls, value):
        return cls._sanitize_text(value, cls.MAX_BIO_LENGTH)

    @field_validator("location", mode="before")
    @classmethod
    def sanitize_location(cls, value):
        return cls._sanitize_text(value, cls.MAX_LOCATION_LENGTH)