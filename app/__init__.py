"""
App module initialization
"""
from app.api import api_router
from app.config import settings

__all__ = ["api_router", "settings"]