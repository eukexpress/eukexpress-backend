from app.api.v1.auth import router as auth_router
from app.api.v1.shipments import router as shipments_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.email import router as email_router
from app.api.v1.public_tracking import router as public_router

__all__ = [
    "auth_router",
    "shipments_router", 
    "dashboard_router",
    "email_router",
    "public_router"
]
