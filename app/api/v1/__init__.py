"""
API v1 Package
"""
from app.api.v1.auth import router as auth
from app.api.v1.dashboard import router as dashboard
from app.api.v1.shipments import router as shipments
from app.api.v1.shipment_detail import router as shipment_detail
from app.api.v1.interventions import router as interventions
from app.api.v1.communication import router as communication
from app.api.v1.bulk_operations import router as bulk_operations
from app.api.v1.public_tracking import router as public_tracking
from app.api.v1.heritage_email import router as heritage_email  # Change from heritage_email_routes to heritage_email