# Eukexpress\backend\app\utils\helpers.py
"""
Helper Functions
Common utility functions used across the application
"""

import re
import json
from datetime import datetime, timedelta, date
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", 
        "NGN": "₦", "JPY": "¥", "CNY": "¥"
    }
    symbol = symbols.get(currency, "")
    return f"{symbol}{amount:,.2f}"

def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime for display"""
    return dt.strftime(format)

def format_date(d: date, format: str = "%Y-%m-%d") -> str:
    """Format date for display"""
    return d.strftime(format)

def parse_json_field(field: Any) -> Optional[Dict]:
    """Parse JSON field safely"""
    if isinstance(field, dict):
        return field
    if isinstance(field, str):
        try:
            return json.loads(field)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON: {field}")
            return None
    return None

def calculate_days_between(start: datetime, end: datetime) -> int:
    """Calculate number of days between two datetimes"""
    delta = end - start
    return delta.days

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to max length with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    # Convert to lowercase
    text = text.lower()
    # Replace spaces with hyphens
    text = re.sub(r'\s+', '-', text)
    # Remove special characters
    text = re.sub(r'[^\w\-]', '', text)
    # Remove multiple hyphens
    text = re.sub(r'\-+', '-', text)
    return text.strip('-')

def extract_initials(name: str) -> str:
    """Extract initials from name"""
    parts = name.split()
    initials = [p[0].upper() for p in parts if p]
    return ''.join(initials[:2])  # Max 2 initials

def mask_email(email: str) -> str:
    """Mask email for display (e.g., j***@gmail.com)"""
    if not email or '@' not in email:
        return email
    local, domain = email.split('@')
    if len(local) <= 2:
        masked = local[0] + '***'
    else:
        masked = local[0] + '***' + local[-1]
    return f"{masked}@{domain}"

def mask_phone(phone: str) -> str:
    """Mask phone number (show last 4 digits)"""
    if not phone:
        return phone
    # Remove non-digits
    digits = re.sub(r'\D', '', phone)
    if len(digits) <= 4:
        return phone
    return '*' * (len(digits) - 4) + digits[-4:]

def generate_reference_number(prefix: str = "REF") -> str:
    """Generate random reference number"""
    import secrets
    import string
    chars = string.ascii_uppercase + string.digits
    suffix = ''.join(secrets.choice(chars) for _ in range(8))
    return f"{prefix}-{suffix}"

def calculate_eta_duration(origin: str, destination: str) -> int:
    """
    Calculate estimated delivery duration in days
    Based on simple rules - can be expanded
    """
    # Simple rules - expand based on actual routes
    if "INTERNATIONAL" in origin or "INTERNATIONAL" in destination:
        return 7  # 7 days for international
    if "EXPRESS" in origin or "EXPRESS" in destination:
        return 2  # 2 days for express
    
    # Default
    return 5  # 5 days standard