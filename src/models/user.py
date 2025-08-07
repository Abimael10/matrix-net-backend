from pydantic import BaseModel

class User(BaseModel):
    id: int | None = None
    username: str
    email: str

#Defining it this way since I dont want to return the password and that only should come from the input
class UserI(User):
    password : str