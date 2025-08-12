from typing import Optional
from datetime import datetime, timezone

from pydantic import BaseModel, EmailStr, field_validator

class User(BaseModel):
    id: int | None = None
    username: str
    email: EmailStr
    bio: str | None = None
    location: str | None = None
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
    #location: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str