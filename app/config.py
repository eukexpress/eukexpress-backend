"""
Environment Configuration Management
Loads and validates all environment variables
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "EukExpress Global Logistics"
    APP_ENV: str = "production"
    APP_SECRET_KEY: str
    APP_DEBUG: bool = False
    APP_URL: str = "https://eukexpress.onrender.com"
    
    # IMPORTANT: Add FRONTEND_URL for QR codes and emails
    FRONTEND_URL: str = "https://eukexpress.com"  # Your frontend domain
    
    # Database - Optimized for Render free tier
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 300
    DATABASE_ECHO: bool = False
    
    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@eukexpress.com"
    ADMIN_PASSWORD: str
    
    # Resend Email
    RESEND_API_KEY: str
    RESEND_FROM_EMAIL: str = "onboarding@delivery.eukexpress.com"
    RESEND_FROM_NAME: str = "EukExpress Global Logistics"
    
    # EukExpress Email
    EUKEXPRESS_RESEND_API_KEY: str
    EUKEXPRESS_FROM_EMAIL: str = "onboarding@delivery.eukexpress.com"
    EUKEXPRESS_FROM_NAME: str = "EukExpress Global Logistics"
    EUKEXPRESS_API_KEY_NAME: Optional[str] = "mail"
    
    # File Uploads - FIXED FOR LOCAL DEVELOPMENT
    MAX_UPLOAD_SIZE: int = 10485760
    ALLOWED_EXTENSIONS: str = ".jpg,.jpeg,.png"
    
    # Use absolute path for local development
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    UPLOAD_PATH: str = os.path.join(os.path.dirname(BASE_DIR), "frontend", "uploads")
    QR_CODE_PATH: str = os.path.join(os.path.dirname(BASE_DIR), "frontend", "qr_codes")
    
    # Security - JWT Settings
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    JWT_ALGORITHM: str = "HS256"
    
    # Session Settings
    SESSION_EXPIRE_MINUTES: int = 60
    
    # CORS
    CORS_ORIGINS: str = "https://eukexpress.com,https://www.eukexpress.com,https://eukexpress.onrender.com,https://eukexpress-backend.onrender.com,http://localhost:8000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:3000,http://127.0.0.1:3000,file://"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_PERIOD: int = 60
    
    # Logging
    LOG_LEVEL: str = "WARNING"
    LOG_FILE: str = os.path.join(BASE_DIR, "logs", "app.log")
    
    # Keep Alive
    RENDER_APP_URL: str = "https://eukexpress.onrender.com"
    KEEP_ALIVE_INTERVAL: int = 10
    KEEP_ALIVE_ENDPOINTS: str = "/,/health,/api/v1/public/status"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    @property
    def keep_alive_endpoints_list(self) -> List[str]:
        return [endpoint.strip() for endpoint in self.KEEP_ALIVE_ENDPOINTS.split(",")]

settings = Settings()

# Ensure directories exist
os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
os.makedirs(settings.QR_CODE_PATH, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_PATH, "invoices"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_PATH, "shipments"), exist_ok=True)