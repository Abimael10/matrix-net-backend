from pydantic import BaseModel, Field
from typing import Optional

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=8)
    new_password: str = Field(..., min_length=8)

class DeleteAccountRequest(BaseModel):
    password: Optional[str] = None  # Optionally require password confirmation
