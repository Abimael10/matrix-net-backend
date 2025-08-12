from typing import Optional

from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: int | None = None
    username: str
    email: EmailStr
    bio: str | None = None
    location: str | None = None

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