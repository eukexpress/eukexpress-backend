"""
API module initialization
"""
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

api_router = auth_router  # Default router

__all__ = [
    "auth_router",
    "shipments_router",
    "dashboard_router",
    "email_router",
    "public_router",
    "communication_router",
    "shipment_detail_router",
    "bulk_operations_router",
    "interventions_router",
    "api_router"
]