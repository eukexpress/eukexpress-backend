# Eukexpress\backend\app\main.py

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

from app.api.v1 import (
    auth, dashboard, shipments, shipment_detail,
    interventions, communication, bulk_operations, public_tracking
)
from app.config import settings
from app.database import engine, Base

# Simple logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("\n" + "="*50)
    print("🚀 EUKEXPRESS API STARTING")
    print("="*50)
    
    # Quick DB check
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database connected")
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    print("="*50 + "\n")
    yield
    
    # Shutdown
    print("\n" + "="*50)
    print("👋 EUKEXPRESS API SHUTDOWN")
    print("="*50 + "\n")

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

# CORS - Using settings.cors_origins_list instead of "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(shipments.router, prefix="/api/v1/shipments", tags=["Shipments"])
app.include_router(shipment_detail.router, prefix="/api/v1/shipments", tags=["Shipment Details"])
app.include_router(interventions.router, prefix="/api/v1/shipments", tags=["Interventions"])
app.include_router(communication.router, prefix="/api/v1/shipments", tags=["Communication"])
app.include_router(bulk_operations.router, prefix="/api/v1/bulk", tags=["Bulk Operations"])
app.include_router(public_tracking.router, prefix="/api/v1/public", tags=["Public"])

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
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)