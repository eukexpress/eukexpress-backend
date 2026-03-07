"""
EukExpress Global Logistics API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime

# Configure logging to be less verbose
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Import all route modules
from app.api.v1 import (
    auth_router,
    shipments_router,
    dashboard_router,
    email_router,
    public_router
)
from app.config import settings
from app.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("\n" + "═"*50)
    print("🚀 EUKEXPRESS API STARTING")
    print("═"*50)
    
    # Quick DB check
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    print("═"*50 + "\n")
    yield
    
    # Shutdown
    print("\n" + "═"*50)
    print("👋 EUKEXPRESS API SHUTDOWN")
    print("═"*50 + "\n")

# Create FastAPI app
app = FastAPI(
    title="EukExpress API",
    description="Logistics Management Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(shipments_router, prefix="/api/v1/shipments", tags=["Shipments"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(email_router, prefix="/api/v1/email", tags=["Email"])
app.include_router(public_router, prefix="/api/v1/public", tags=["Public Tracking"])

# Static files
os.makedirs(settings.UPLOAD_PATH, exist_ok=True)
os.makedirs(settings.QR_CODE_PATH, exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_PATH, "shipments"), exist_ok=True)
os.makedirs(os.path.join(settings.UPLOAD_PATH, "invoices"), exist_ok=True)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_PATH), name="uploads")
app.mount("/qr", StaticFiles(directory=settings.QR_CODE_PATH), name="qr")

@app.get("/")
async def root():
    return {
        "app": "EukExpress API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.APP_ENV,
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)