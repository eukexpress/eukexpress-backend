# Eukexpress\backend\app\services\notification_service.py
"""
Notification Service - Email Trigger Management
Automatically sends emails based on events
"""

import logging
from sqlalchemy.orm import Session
from datetime import datetime

from app.services import email_service
from app.models import Shipment

logger = logging.getLogger(__name__)

async def trigger_status_change_notifications(
    shipment: Shipment,
    old_status: str,
    new_status: str,
    db: Session
):
    """
    Send appropriate emails based on status change
    """
    logger.info(f"Triggering notifications for {shipment.tracking_number}: {old_status} -> {new_status}")
    
    # BOOKED → send invoice
    if new_status == "BOOKED" and old_status != "BOOKED":
        await email_service.send_invoice(shipment, db)
    
    # CUSTOMS_BOND activated → send customs notice
    elif new_status == "CUSTOMS_BOND" and old_status != "CUSTOMS_BOND":
        await email_service.send_customs_bond_notification(shipment, db)
    
    # CUSTOMS_CLEARED → send clearance notice
    elif new_status == "CUSTOMS_CLEARED":
        # Calculate duration in customs
        duration = None
        if shipment.customs_bond_activated_at:
            duration = datetime.utcnow() - shipment.customs_bond_activated_at
        await email_service.send_customs_released_notification(shipment, duration, db)
    
    # DELIVERED → send delivery confirmation
    elif new_status == "DELIVERED":
        await email_service.send_delivery_confirmation(shipment, db)
    
    # RETURN_TO_SENDER initiated
    elif new_status == "RETURN_TO_SENDER" and old_status != "RETURN_TO_SENDER":
        await email_service.send_return_notification(shipment, db)

async def trigger_intervention_notifications(
    shipment: Shipment,
    intervention_type: str,
    action: str,
    db: Session,
    **kwargs
):
    """
    Send emails for intervention toggles
    """
    logger.info(f"Triggering intervention notifications for {shipment.tracking_number}: {intervention_type} - {action}")
    
    if intervention_type == "customs":
        if action == "activate":
            await email_service.send_customs_bond_notification(shipment, db)
        elif action == "release":
            duration = kwargs.get('duration')
            await email_service.send_customs_released_notification(shipment, duration, db)
    
    elif intervention_type == "security":
        if action == "activate":
            await email_service.send_security_hold_notification(shipment, db)
        elif action == "clear":
            await email_service.send_security_cleared_notification(shipment, db)
    
    elif intervention_type == "damage":
        if action == "report":
            await email_service.send_damage_report_notification(shipment, db)
        elif action == "resolve":
            await email_service.send_damage_resolved_notification(shipment, db)
    
    elif intervention_type == "delay":
        if action == "report":
            reason = kwargs.get('reason', 'Unknown reason')
            revised_eta = kwargs.get('revised_eta')
            await email_service.send_delay_notification(shipment, reason, revised_eta, db)