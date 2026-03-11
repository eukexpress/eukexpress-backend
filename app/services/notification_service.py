"""
Notification Service - Email Trigger Management
Automatically sends emails based on events
"""

import logging
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.email_service import email_service
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
    logger.info(f"📧 Triggering status change notifications for {shipment.tracking_number}: {old_status} -> {new_status}")
    
    try:
        # Use email_service directly instead of notification_service
        await email_service.send_status_update_notification(
            shipment, old_status, new_status, None, None
        )
        logger.info(f"✅ Status change emails sent for {shipment.tracking_number}")
    except Exception as e:
        logger.error(f"❌ Failed to send status change emails: {e}", exc_info=True)

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
    logger.info(f"📧 Triggering intervention notifications for {shipment.tracking_number}: {intervention_type} - {action}")
    
    try:
        # Route to appropriate email service method
        if intervention_type == "customs":
            await email_service.send_customs_notification(shipment, action, kwargs)
        elif intervention_type == "security":
            await email_service.send_security_notification(
                shipment, action, 
                location=kwargs.get('location'),
                notes=kwargs.get('notes')
            )
        elif intervention_type == "damage":
            await email_service.send_damage_notification(
                shipment, action,
                description=kwargs.get('description'),
                resolution=kwargs.get('resolution')
            )
        elif intervention_type == "return":
            await email_service.send_return_notification(
                shipment,
                reason=kwargs.get('reason')
            )
        elif intervention_type == "delay":
            await email_service.send_delay_notification(
                shipment, action,
                reason=kwargs.get('reason'),
                revised_eta=kwargs.get('revised_eta')
            )
        
        logger.info(f"✅ Intervention emails sent for {shipment.tracking_number}")
    except Exception as e:
        logger.error(f"❌ Failed to send intervention emails: {e}", exc_info=True)

async def send_shipment_created_notification(shipment: Shipment):
    """Send invoice to sender and notification to recipient"""
    logger.info(f"📧 Sending creation notifications for {shipment.tracking_number}")
    
    try:
        # Send invoice to sender (will be handled by email_service.send_invoice_pdf separately)
        # Send notification to recipient
        await email_service.send_shipment_created_notification(shipment)
        logger.info(f"✅ Shipment creation emails sent for {shipment.tracking_number}")
    except Exception as e:
        logger.error(f"❌ Failed to send creation emails: {e}", exc_info=True)