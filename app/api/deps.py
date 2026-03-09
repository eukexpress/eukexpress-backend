#app/api/deps.py
"""
Authentication Dependencies
Unified auth handling for all endpoints
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging
import traceback

from app.database import get_db
from app.services.auth_service import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)

async def get_current_user_optional(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Get current user from either OAuth2 scheme or Authorization header
    Returns None if no valid user found
    """
    # Try to get token from OAuth2 scheme first
    extracted_token = token
    
    # If no token from OAuth2, try to get from Authorization header directly
    if not extracted_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            extracted_token = auth_header[7:]  # Remove "Bearer " prefix
    
    if not extracted_token:
        return None
    
    # Get current user
    try:
        user = get_current_user(extracted_token, db)
        return user
    except Exception as e:
        logger.error(f"Error in get_current_user: {str(e)}")
        return None

async def get_current_user_required(
    current_user = Depends(get_current_user_optional)
):
    """
    Require authenticated user
    Raises 401 if no valid user found
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user