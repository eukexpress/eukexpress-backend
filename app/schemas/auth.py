"""
Authentication Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    id: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class AdminResponse(BaseModel):
    id: str
    username: str
    email: str
    last_login: Optional[datetime] = None
    last_login_ip: Optional[str] = None

    class Config:
        from_attributes = True
