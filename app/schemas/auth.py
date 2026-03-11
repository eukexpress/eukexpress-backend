"""
Authentication Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int] = None
    admin_id: Optional[str] = None
    admin_username: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None
    id: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    admin_id: str
    admin_username: str

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