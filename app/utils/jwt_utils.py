# Eukexpress\backend\app\utils\jwt_utils.py
"""
JWT Utilities
Token creation, validation, and management
"""

from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

from app.config import settings

logger = logging.getLogger(__name__)

def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.APP_SECRET_KEY, 
            algorithm="HS256"
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to create access token: {e}")
        raise

def create_refresh_token(data: Dict) -> str:
    """
    Create JWT refresh token (longer expiry)
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    try:
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.APP_SECRET_KEY, 
            algorithm="HS256"
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Failed to create refresh token: {e}")
        raise

def decode_token(token: str) -> Optional[Dict]:
    """
    Decode and validate JWT token
    """
    try:
        payload = jwt.decode(
            token, 
            settings.APP_SECRET_KEY, 
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.error(f"Token validation error: {e}")
        return None

def verify_token(token: str, token_type: str = "access") -> bool:
    """
    Verify token is valid and of correct type
    """
    payload = decode_token(token)
    if not payload:
        return False
    
    return payload.get("type") == token_type

def get_token_payload(token: str) -> Optional[Dict]:
    """
    Get token payload without validation
    Use for debugging only
    """
    try:
        return jwt.get_unverified_claims(token)
    except Exception as e:
        logger.error(f"Failed to get token payload: {e}")
        return None

def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Create new access token from refresh token
    """
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        logger.warning("Invalid refresh token")
        return None
    
    # Create new access token
    new_token_data = {
        "sub": payload.get("sub"),
        "id": payload.get("id")
    }
    
    return create_access_token(new_token_data)

def blacklist_token(token: str):
    """
    Add token to blacklist (for logout)
    Note: Requires Redis or database storage for production
    """
    # TODO: Implement token blacklist with Redis
    pass