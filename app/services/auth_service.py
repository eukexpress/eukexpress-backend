"""
Authentication Service
Handles JWT token creation, validation, session management and password management
"""

from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import traceback
import time

from app.config import settings
from app.models.admin import Admin

# Configure logging - set to WARNING in production
if settings.APP_ENV == "production":
    logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.DEBUG)
    
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simple in-memory token blacklist and session store
token_blacklist = set()
session_store = {}  # user_id -> last_activity timestamp

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def authenticate_admin(db: Session, username: str, password: str):
    """Authenticate admin by username and password"""
    start_time = time.time()
    
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin:
        logger.warning(f"Authentication failed: user not found - {username}")
        return None
    
    if not verify_password(password, admin.password_hash):
        logger.warning(f"Authentication failed: invalid password - {username}")
        return None
    
    # Update session activity
    session_store[str(admin.id)] = datetime.utcnow().timestamp()
    
    elapsed = time.time() - start_time
    logger.info(f"Authentication successful for {username} in {elapsed:.3f}s")
    
    return admin

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token with session expiry"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add issued at and session ID
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "session_id": str(time.time())  # Unique session identifier
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.APP_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    """Decode and validate JWT token"""
    if not token:
        return None
    
    try:
        # Clean token if it has Bearer prefix
        if token.startswith('Bearer '):
            token = token[7:]
        
        # Check if token is blacklisted
        if token in token_blacklist:
            logger.warning("Token is blacklisted")
            return None
        
        # Decode the token
        payload = jwt.decode(
            token, 
            settings.APP_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Check session activity
        user_id = payload.get("id")
        if user_id and user_id in session_store:
            last_activity = session_store[user_id]
            now = datetime.utcnow().timestamp()
            
            # Check if session expired due to inactivity
            if now - last_activity > settings.SESSION_EXPIRE_MINUTES * 60:
                logger.warning(f"Session expired for user {user_id} due to inactivity")
                return None
            
            # Update last activity
            session_store[user_id] = now
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.JWTError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected decode error: {e}")
        return None

def get_current_user(token: str, db: Session):
    """Get current user from token"""
    if not token:
        return None
    
    payload = decode_token(token)
    if not payload:
        return None
    
    username = payload.get("sub")
    if not username:
        return None
    
    admin = db.query(Admin).filter(Admin.username == username).first()
    return admin

def update_last_login(db: Session, admin_id: str, ip_address: str):
    """Update admin's last login timestamp and IP"""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if admin:
        admin.last_login = datetime.utcnow()
        admin.last_login_ip = ip_address
        db.commit()
        
        # Update session activity
        session_store[admin_id] = datetime.utcnow().timestamp()

def change_password(db: Session, admin_id: str, current_password: str, new_password: str) -> bool:
    """Change admin password"""
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        return False
    
    if not verify_password(current_password, admin.password_hash):
        return False
    
    admin.password_hash = get_password_hash(new_password)
    admin.updated_at = datetime.utcnow()
    db.commit()
    
    return True

def logout_user(token: str):
    """Logout user by blacklisting their token"""
    if token:
        if token.startswith('Bearer '):
            token = token[7:]
        token_blacklist.add(token)
        logger.info(f"User logged out, token blacklisted")

def cleanup_expired_sessions():
    """Clean up expired sessions (call periodically)"""
    now = datetime.utcnow().timestamp()
    expired_users = []
    
    for user_id, last_activity in session_store.items():
        if now - last_activity > settings.SESSION_EXPIRE_MINUTES * 60 * 24:  # 24 hours
            expired_users.append(user_id)
    
    for user_id in expired_users:
        del session_store[user_id]
        logger.debug(f"Cleaned up expired session for user {user_id}")