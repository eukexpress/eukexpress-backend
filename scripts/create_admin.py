# Eukexpress\backend\scripts\create_admin.py
#!/usr/bin/env python3
"""
Create Admin User Script
Run this script to create the first admin user
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import Admin
from app.services.auth_service import get_password_hash
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin():
    """Create the initial admin user"""
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(Admin).first()
        if admin:
            logger.info("Admin user already exists")
            return
        
        # Create new admin
        hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
        admin = Admin(
            username=settings.ADMIN_USERNAME,
            email=settings.ADMIN_EMAIL,
            password_hash=hashed_password
        )
        
        db.add(admin)
        db.commit()
        
        logger.info(f"Admin user created successfully: {settings.ADMIN_USERNAME}")
        logger.info(f"Email: {settings.ADMIN_EMAIL}")
        
    except Exception as e:
        logger.error(f"Failed to create admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()