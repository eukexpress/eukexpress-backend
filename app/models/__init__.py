# Eukexpress\backend\app\models\__init__.py
"""
Models Package Initialization
Export all models for easy importing
"""

from app.models.admin import Admin
from app.models.shipment import Shipment
from app.models.status_history import StatusHistory
from app.models.intervention_log import InterventionLog
from app.models.email_log import EmailLog
from app.models.bulk_email_campaign import BulkEmailCampaign

__all__ = [
    'Admin',
    'Shipment',
    'StatusHistory',
    'InterventionLog',
    'EmailLog',
    'BulkEmailCampaign'
]