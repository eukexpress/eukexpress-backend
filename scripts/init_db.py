# Eukexpress\backend\scripts\init_db.py
#!/usr/bin/env python3
"""
Database Initialization Script
Run this script to initialize the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import Admin, Shipment, StatusHistory, InterventionLog, EmailLog
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize database - create all tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    init_db()