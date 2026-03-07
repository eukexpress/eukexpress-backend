from app.api.v1 import (
    auth_router,
    shipments_router,
    dashboard_router,
    email_router,
    public_router
)

__all__ = [
    "auth_router",
    "shipments_router",
    "dashboard_router",
    "email_router",
    "public_router"
]
