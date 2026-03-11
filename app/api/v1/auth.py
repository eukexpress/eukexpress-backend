"""
Authentication Endpoints
Admin login, logout, and password management with session tracking
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import logging
import time

from app.database import get_db
from app.services.auth_service import (
    authenticate_admin,
    create_access_token,
    get_current_user,
    change_password,
    update_last_login,
    logout_user
)
from app.schemas.auth import Token, ChangePasswordRequest, LoginResponse, TokenData
from app.config import settings

router = APIRouter(tags=["Authentication"])
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login with username and password (form data)"""
    start_time = time.time()
    
    try:
        # Authenticate admin
        admin = authenticate_admin(db, form_data.username, form_data.password)
        if not admin:
            logger.warning(f"Failed login attempt for: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        client_ip = request.client.host if request.client else "unknown"
        update_last_login(db, admin.id, client_ip)
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": admin.username, "id": str(admin.id)},
            expires_delta=access_token_expires
        )
        
        elapsed = time.time() - start_time
        logger.info(f"Login successful for {admin.username} in {elapsed:.3f}s")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "admin_id": str(admin.id),
            "admin_username": admin.username
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Logout - blacklist the current token"""
    if token:
        logout_user(token)
    return {"message": "Successfully logged out", "success": True}

@router.get("/verify")
async def verify_token(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Verify if token is valid and get session info"""
    start_time = time.time()
    
    try:
        admin = get_current_user(token, db)
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Get token expiry info
        from jose import jwt
        clean_token = token.replace('Bearer ', '') if token.startswith('Bearer ') else token
        payload = jwt.decode(
            clean_token,
            settings.APP_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False}
        )
        
        exp_timestamp = payload.get("exp", 0)
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        expires_in = max(0, int((exp_datetime - now).total_seconds()))
        
        elapsed = time.time() - start_time
        
        return {
            "valid": True,
            "username": admin.username,
            "id": str(admin.id),
            "expires_in": expires_in,
            "verified_in": f"{elapsed:.3f}s"
        }
        
    except HTTPException:
        raise
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
        
        # Force logout after password change
        logout_user(token)
        
        return {"message": "Password changed successfully", "success": True}
        
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