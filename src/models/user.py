from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: int | None = None
    username: str
    email: EmailStr

class UserI(User):
    password : str

class UserLogin(BaseModel):
    email: EmailStr
    password: str