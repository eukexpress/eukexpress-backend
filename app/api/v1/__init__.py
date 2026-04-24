"""
API v1 - Router Exports
"""
from app.api.v1.auth import auth_router
from app.api.v1.shipments import shipments_router
from app.api.v1.dashboard import dashboard_router
from app.api.v1.email import email_router
from app.api.v1.public_tracking import public_router
from app.api.v1.communication import router as communication_router
from app.api.v1.shipment_detail import router as shipment_detail_router
from app.api.v1.bulk_operations import router as bulk_operations_router
from app.api.v1.interventions import router as interventions_router
from app.api.v1.heritage import heritage_router

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
    "heritage_router"
]
