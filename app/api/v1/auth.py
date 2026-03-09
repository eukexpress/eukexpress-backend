#app/api/v1/auth.py
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
from app.services import (
    authenticate_admin,
    create_access_token,
    get_current_user,
    change_password,
    update_last_login
)
from app.schemas.auth import Token, ChangePasswordRequest
from app.config import settings

router = APIRouter(tags=["Authentication"])
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login with username and password (form data)"""
    try:
        # Authenticate admin
        admin = authenticate_admin(db, form_data.username, form_data.password)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        client_ip = request.client.host if request.client else "unknown"
        update_last_login(db, admin.id, client_ip)
        
        # Get token expiry
        token_expiry_minutes = getattr(settings, 'JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 
                                       getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 30))
        
        # Create access token
        access_token_expires = timedelta(minutes=token_expiry_minutes)
        access_token = create_access_token(
            data={"sub": admin.username, "id": str(admin.id)},
            expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/logout")
async def logout():
    """Logout (client-side only - token just expires)"""
    return {"message": "Successfully logged out"}

@router.get("/verify")
async def verify_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Verify if token is valid"""
    try:
        admin = get_current_user(token, db)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return {
            "valid": True,
            "username": admin.username,
            "id": str(admin.id)
        }
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@router.post("/change-password")
async def change_admin_password(
    request: ChangePasswordRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Change password for authenticated admin"""
    try:
        admin = get_current_user(token, db)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        success = change_password(
            db,
            admin.id,
            request.current_password,
            request.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/me")
async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get current admin info"""
    try:
        admin = get_current_user(token, db)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        return {
            "id": str(admin.id),
            "username": admin.username,
            "email": admin.email,
            "last_login": admin.last_login.isoformat() if admin.last_login else None,
            "last_login_ip": admin.last_login_ip
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current admin error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# Export router with expected name
auth_router = router