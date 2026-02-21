# backend/app/config.py
"""
Environment Configuration Management
Loads and validates all environment variables
"""

from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "EukExpress Global Logistics"
    APP_ENV: str = "production"  # Changed to production
    APP_SECRET_KEY: str
    APP_DEBUG: bool = False
    APP_URL: str = "https://eukexpress.onrender.com"  # Your Render URL
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@eukexpress.com"
    ADMIN_PASSWORD: str
    
    # Resend Email - IMPORTANT: Using onboarding@ as required by Resend
    RESEND_API_KEY: str
    RESEND_FROM_EMAIL: str = "onboarding@eukexpress.com"  # Must match Resend verified domain
    RESEND_FROM_NAME: str = "EukExpress Global Logistics"
    
    # File Uploads - Render Linux paths
    MAX_UPLOAD_SIZE: int = 10485760  # 10MB
    ALLOWED_EXTENSIONS: str = ".jpg,.jpeg,.png"
    UPLOAD_PATH: str = "/opt/render/project/src/frontend/uploads"
    QR_CODE_PATH: str = "/opt/render/project/src/frontend/qr_codes"
    
    # Security
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "https://eukexpress.onrender.com,https://www.eukexpress.com,http://localhost:8000"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/opt/render/project/src/backend/logs/app.log"
    
    # Keep Alive
    RENDER_APP_URL: str = "https://eukexpress.onrender.com"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Convert ALLOWED_EXTENSIONS string to list"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

# Create global settings instance
settings = Settings()

# Ensure directories exist
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
os.makedirs(settings.QR_CODE_PATH, exist_ok=True)