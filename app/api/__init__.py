"""
API Package
"""
from app.api.v1 import (
    auth, 
    dashboard, 
    shipments, 
    shipment_detail,
    interventions, 
    communication, 
    bulk_operations, 
    public_tracking,
    heritage_email  # Change from heritage_email_routes to heritage_email
)