# Eukexpress\backend\app\utils\tracking_generator.py
"""
Tracking Number Generator
Generates unique tracking numbers in format EUKXXXXX
"""

import secrets
import string
import time
from sqlalchemy.orm import Session
from app.models import Shipment

# Tracking number format: EUK + 5 characters from allowed set
TRACKING_PREFIX = "EUK"
ALLOWED_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Removed I, O, Q, 0, 1 for clarity
TRACKING_LENGTH = 8  # Total including prefix

def generate_tracking_number() -> str:
    """
    Generate random 8-character tracking number
    Format: EUKXXXXX where X is from ALLOWED_CHARS
    Uses secrets module for cryptographic randomness
    """
    suffix = ''.join(secrets.choice(ALLOWED_CHARS) for _ in range(5))
    return f"{TRACKING_PREFIX}{suffix}"

def validate_tracking_format(tracking: str) -> bool:
    """
    Validate tracking number format
    Returns True if format is valid
    """
    import re
    pattern = r'^EUK[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{5}$'
    return bool(re.match(pattern, tracking))

def generate_unique_tracking(db: Session, max_attempts: int = 10) -> str:
    """
    Generate unique tracking number with collision check
    Tries up to max_attempts times, then falls back to timestamp-based
    """
    for attempt in range(max_attempts):
        tracking = generate_tracking_number()
        existing = db.query(Shipment).filter(
            Shipment.tracking_number == tracking
        ).first()
        
        if not existing:
            return tracking
    
    # Fallback: add timestamp to ensure uniqueness
    timestamp = int(time.time()) % 1000
    tracking = f"EUK{secrets.choice(ALLOWED_CHARS)}{timestamp:03d}"
    return tracking

def generate_invoice_number(tracking_number: str) -> str:
    """
    Generate invoice number based on tracking number
    Format: INV-YYYYMMDD-XXXXX
    """
    from datetime import datetime
    date_part = datetime.now().strftime("%Y%m%d")
    tracking_part = tracking_number[-5:]
    return f"INV-{date_part}-{tracking_part}"