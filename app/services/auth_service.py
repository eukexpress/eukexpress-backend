# Eukexpress\backend\app\services\auth_service.py
"""
Authentication Service
Handles JWT token creation, validation, and password management
"""

from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.config import settings
from app.models import Admin

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Logger
logger = logging.getLogger(__name__)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def authenticate_admin(db: Session, username: str, password: str):
    """Authenticate admin by username and password"""
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin:
        return None
    if not verify_password(password, admin.password_hash):
        return None
    return admin

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.APP_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

def decode_token(token: str):
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError as e:
        logger.error(f"Token decode error: {e}")
        return None

def update_last_login(db: Session, admin_id: str, ip_address: str):
    """Update admin's last login timestamp and IP"""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if admin:
        admin.last_login = datetime.utcnow()
        admin.last_login_ip = ip_address
        db.commit()

def change_password(db: Session, admin_id: str, current_password: str, new_password: str) -> bool:
    """Change admin password"""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        return False
    
    # Verify current password
    if not verify_password(current_password, admin.password_hash):
        return False
    
    # Update to new password
    admin.password_hash = get_password_hash(new_password)
    admin.updated_at = datetime.utcnow()
    db.commit()
    
    return True