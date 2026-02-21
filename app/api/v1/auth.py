# Eukexpress\backend\app\api\v1\auth.py
"""
Authentication Endpoints
Admin login, logout, and password management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import logging

from app.database import get_db
from app.services import auth_service
from app.schemas.admin import AdminLogin, TokenResponse, PasswordChange
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Admin login endpoint
    Returns JWT token for authentication
    """
    logger.info(f"Login attempt for user: {form_data.username}")
    
    # Authenticate user
    admin = auth_service.authenticate_admin(
        db, 
        form_data.username, 
        form_data.password
    )
    
    if not admin:
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login info
    client_ip = request.client.host
    auth_service.update_last_login(db, admin.id, client_ip)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": admin.username, "id": str(admin.id)},
        expires_delta=access_token_expires
    )
    
    logger.info(f"Successful login for user: {form_data.username}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "admin_id": str(admin.id),
        "admin_username": admin.username
    }

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """
    Logout endpoint - invalidate token
    Note: With JWT, we can't truly invalidate without a blacklist
    This is a placeholder for future implementation with token blacklist
    """
    # In a production system, you might want to add the token to a blacklist
    logger.info("User logged out")
    return {"message": "Logged out successfully"}

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Change admin password
    Requires current password verification
    """
    # Get current admin from token
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    admin_id = payload.get("id")
    
    # Verify current password and update
    success = auth_service.change_password(
        db,
        admin_id,
        password_data.current_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    logger.info(f"Password changed for admin: {admin_id}")
    return {"message": "Password updated successfully"}

@router.get("/verify")
async def verify_token(token: str = Depends(oauth2_scheme)):
    """
    Verify if token is valid
    Used by frontend to check authentication status
    """
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return {
        "valid": True,
        "username": payload.get("sub"),
        "admin_id": payload.get("id")
    }