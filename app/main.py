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

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Import all route modules
from app.api.v1 import (
    auth_router,
    shipments_router,
    dashboard_router,
    email_router,
    public_router,
    communication_router,
    shipment_detail_router,
    bulk_operations_router,
    interventions_router
)
from app.config import settings
from app.database import engine, Base, check_database_connection
from app.services.keep_alive import keep_alive_service, start_keep_alive

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("\n" + "═"*60)
    print("🚀 EUKEXPRESS API STARTING")
    print("═"*60)
    
    # Quick DB check
    try:
        Base.metadata.create_all(bind=engine)
        db_status = check_database_connection()
        if db_status:
            print("✅ Database connected")
        else:
            print("⚠️ Database connection issue")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    # Start keep-alive service (only in production)
    if settings.APP_ENV == "production":
        await start_keep_alive()
        print(f"✅ Keep-alive service started (every {settings.KEEP_ALIVE_INTERVAL} minutes)")
    
    print("═"*60 + "\n")
    yield
    
    # Shutdown
    print("\n" + "═"*60)
    print("👋 EUKEXPRESS API SHUTDOWN")
    print("═"*60)
    
    if settings.APP_ENV == "production":
        await keep_alive_service.stop()
    
    print("✅ Cleanup complete\n")

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

# ============================================
# CORS CONFIGURATION
# ============================================
ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "https://eukexpress.com",
    "https://www.eukexpress.com",
]

if hasattr(settings, 'cors_origins_list') and settings.cors_origins_list:
    ALLOWED_ORIGINS.extend(settings.cors_origins_list)

ALLOWED_ORIGINS = list(set(ALLOWED_ORIGINS))

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Routes
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(shipments_router, prefix="/api/v1/shipments", tags=["Shipments"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(email_router, prefix="/api/v1/email", tags=["Email"])
app.include_router(public_router, prefix="/api/v1/public", tags=["Public Tracking"])
app.include_router(communication_router, prefix="/api/v1/shipments", tags=["Communication"])
app.include_router(shipment_detail_router, prefix="/api/v1/shipments", tags=["Shipment Details"])
app.include_router(bulk_operations_router, prefix="/api/v1/bulk", tags=["Bulk Operations"])
app.include_router(interventions_router, prefix="/api/v1/shipments", tags=["Interventions"])

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
        "docs": "/docs",
        "keep_alive": f"Active (every {settings.KEEP_ALIVE_INTERVAL} minutes)" if settings.APP_ENV == "production" else "Disabled"
    }

@app.get("/health")
async def health():
    db_status = check_database_connection()
    return {
        "status": "ok" if db_status else "degraded",
        "time": datetime.utcnow().isoformat(),
        "database": "connected" if db_status else "disconnected",
        "environment": settings.APP_ENV
    }

@app.get("/api/v1/public/status")
async def public_status():
    """Public endpoint for keep-alive pings"""
    return {
        "status": "operational",
        "service": "EukExpress API",
        "timestamp": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="warning",
        access_log=False
    )