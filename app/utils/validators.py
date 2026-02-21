# Eukexpress\backend\app\utils\validators.py
"""
Input Validation Utilities
Validates all incoming data
"""

import re
from datetime import date, datetime
from typing import Dict, Any, Optional
from decimal import Decimal

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number (international format)"""
    # Allows +, numbers, spaces, hyphens, parentheses
    pattern = r'^[\+\d\s\-\(\)]{5,20}$'
    return bool(re.match(pattern, phone))

def validate_tracking(tracking: str) -> bool:
    """Validate tracking number format"""
    pattern = r'^EUK[ABCDEFGHJKLMNPQRSTUVWXYZ23456789]{5}$'
    return bool(re.match(pattern, tracking))

def validate_dimensions(dimensions: Dict[str, float]) -> bool:
    """Validate dimensions object"""
    required_keys = ['length', 'width', 'height']
    if not all(key in dimensions for key in required_keys):
        return False
    
    for key in required_keys:
        if not isinstance(dimensions[key], (int, float)) or dimensions[key] <= 0:
            return False
    
    return True

def validate_weight(weight: float) -> bool:
    """Validate weight (positive number)"""
    return isinstance(weight, (int, float)) and weight > 0

def validate_date_range(start_date: date, end_date: date) -> bool:
    """Validate that end date is after start date"""
    return end_date >= start_date

def validate_payment_amount(amount: Decimal) -> bool:
    """Validate payment amount (positive)"""
    return amount > 0

def validate_image_file(filename: str) -> bool:
    """Validate image file extension"""
    allowed_extensions = ['.jpg', '.jpeg', '.png']
    ext = filename.lower()
    return any(ext.endswith(allowed) for allowed in allowed_extensions)

def sanitize_input(text: str) -> str:
    """Basic input sanitization"""
    # Remove any HTML tags
    import re
    clean = re.sub(r'<[^>]*>', '', text)
    # Escape special characters
    clean = clean.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return clean.strip()