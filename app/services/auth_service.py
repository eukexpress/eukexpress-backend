"""
Authentication Service
Handles JWT token creation, validation, and password management
"""

from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
import traceback

from app.config import settings
from app.models.admin import Admin

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def authenticate_admin(db: Session, username: str, password: str):
    """Authenticate admin by username and password"""
    logger.debug(f"🔐 Authenticating admin: {username}")
    admin = db.query(Admin).filter(Admin.username == username).first()
    if not admin:
        logger.debug(f"🔐 Admin not found: {username}")
        return None
    if not verify_password(password, admin.password_hash):
        logger.debug(f"🔐 Invalid password for: {username}")
        return None
    logger.debug(f"🔐 Authentication successful: {username}")
    return admin

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.APP_SECRET_KEY, algorithm="HS256")
    logger.debug(f"🔑 Created token for user: {data.get('sub')}")
    return encoded_jwt

def decode_token(token: str):
    """Decode and validate JWT token"""
    logger.debug("="*60)
    logger.debug("🔑 DECODE TOKEN - START")
    logger.debug(f"🔑 Input token length: {len(token) if token else 0}")
    logger.debug(f"🔑 Token preview: {token[:50] if token and len(token) > 50 else token}...")
    
    if not token:
        logger.error("🔑 No token provided to decode")
        return None
    
    try:
        # Check if token has Bearer prefix
        if token.startswith('Bearer '):
            logger.debug("🔑 Token has 'Bearer ' prefix - cleaning...")
            token = token[7:]
            logger.debug(f"🔑 Cleaned token: {token[:50]}...")
        
        # Validate token format
        if token.count('.') != 2:
            logger.error(f"🔑 Invalid JWT format - has {token.count('.')} dots, expected 2")
            return None
        
        # Log secret key being used (first few chars only)
        logger.debug(f"🔑 Using secret key: {settings.APP_SECRET_KEY[:10]}...")
        
        # Decode the token
        payload = jwt.decode(token, settings.APP_SECRET_KEY, algorithms=["HS256"])
        
        logger.debug(f"🔑 Token decoded successfully!")
        logger.debug(f"🔑 Payload: {payload}")
        logger.debug(f"🔑 Expiration: {datetime.fromtimestamp(payload.get('exp', 0))}")
        
        # Check expiration
        exp = payload.get('exp')
        if exp:
            exp_time = datetime.fromtimestamp(exp)
            now = datetime.utcnow()
            if exp_time < now:
                logger.error(f"🔑 Token expired at {exp_time}, now is {now}")
                return None
            logger.debug(f"🔑 Token valid until: {exp_time}")
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.error("🔑 Token expired signature error")
        return None
    except jwt.InvalidTokenError as e:
        logger.error(f"🔑 Invalid token error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"🔑 Unexpected decode error: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def get_current_user(token: str, db: Session):
    """Get current user from token"""
    logger.debug("="*60)
    logger.debug("🔐 GET CURRENT USER CALLED")
    logger.debug(f"🔐 Token received - Length: {len(token) if token else 0}")
    logger.debug(f"🔐 Token preview: {token[:50] if token and len(token) > 50 else token}...")
    
    if not token:
        logger.error("🔐 No token provided")
        return None
    
    try:
        # Log token format
        if token.startswith('Bearer '):
            logger.warning("🔐 Token has 'Bearer ' prefix - cleaning...")
            token = token[7:]
            logger.debug(f"🔐 Cleaned token: {token[:50]}...")
        
        # Check if token looks like a JWT (has dots)
        if token.count('.') == 2:
            logger.debug("🔐 Token format: Valid JWT (3 parts)")
        else:
            logger.warning(f"🔐 Token format: Invalid JWT - has {token.count('.')} dots")
        
        # Decode token
        logger.debug("🔐 Attempting to decode token...")
        payload = decode_token(token)
        
        if not payload:
            logger.error("🔐 Failed to decode token")
            return None
        
        # Extract username
        username = payload.get("sub")
        if not username:
            logger.error("🔐 No username (sub) in token payload")
            logger.error(f"🔐 Available payload keys: {list(payload.keys())}")
            return None
        
        logger.debug(f"🔐 Looking up user: '{username}'")
        
        # Query database
        admin = db.query(Admin).filter(Admin.username == username).first()
        
        if not admin:
            logger.error(f"🔐 User '{username}' not found in database")
            # Log available users for debugging
            all_admins = db.query(Admin.username, Admin.id).all()
            logger.debug(f"🔐 Available users in DB: {[{'username': a[0], 'id': str(a[1])} for a in all_admins]}")
            return None
        
        logger.debug(f"🔐 ✅ SUCCESS! User found: {admin.username} (ID: {admin.id})")
        logger.debug(f"🔐 User details - Created: {admin.created_at}, Last login: {admin.last_login}")
        
        return admin
        
    except Exception as e:
        logger.error(f"🔐 Unexpected error in get_current_user: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def update_last_login(db: Session, admin_id: str, ip_address: str):
    """Update admin's last login timestamp and IP"""
    logger.debug(f"📝 Updating last login for admin ID: {admin_id}, IP: {ip_address}")
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if admin:
        admin.last_login = datetime.utcnow()
        admin.last_login_ip = ip_address
        db.commit()
        logger.debug(f"📝 Last login updated for: {admin.username}")
    else:
        logger.error(f"📝 Admin not found with ID: {admin_id}")

def change_password(db: Session, admin_id: str, current_password: str, new_password: str) -> bool:
    """Change admin password"""
    logger.debug(f"🔐 Password change requested for admin ID: {admin_id}")
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        logger.error(f"🔐 Admin not found with ID: {admin_id}")
        return False
    
    if not verify_password(current_password, admin.password_hash):
        logger.error("🔐 Current password is incorrect")
        return False
    
    admin.password_hash = get_password_hash(new_password)
    admin.updated_at = datetime.utcnow()
    db.commit()
    
    logger.debug(f"🔐 Password changed successfully for: {admin.username}")
    return True