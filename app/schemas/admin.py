# Eukexpress\backend\app\schemas\admin.py
"""
Admin Pydantic Schemas
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid

class AdminBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class AdminCreate(AdminBase):
    password: str = Field(..., min_length=8)

class AdminLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    admin_id: str
    admin_username: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)

class AdminResponse(AdminBase):
    id: uuid.UUID
    created_at: datetime
    last_login: Optional[datetime]
    last_login_ip: Optional[str]

    class Config:
        from_attributes = True