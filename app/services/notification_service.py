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
    
    # Create HTML content
    html_content = f"""
    <h2>Shipment Status Update</h2>
    <p>Your shipment <strong>{shipment.tracking_number}</strong> has been updated.</p>
    <p><strong>Old Status:</strong> {old_status}</p>
    <p><strong>New Status:</strong> {new_status}</p>
    <p><strong>Origin:</strong> {shipment.origin_location}</p>
    <p><strong>Destination:</strong> {shipment.destination_location}</p>
    <p>Track your shipment at: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">https://eukexpress.com/track?number={shipment.tracking_number}</a></p>
    """
    
    # Send to sender
    await email_service.send_email(
        to=[shipment.sender_email],
        subject=f"Shipment {shipment.tracking_number} Status Update",
        html_content=html_content
    )
    
    # Send to recipient
    await email_service.send_email(
        to=[shipment.recipient_email],
        subject=f"Shipment {shipment.tracking_number} Status Update",
        html_content=html_content
    )

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
    
    intervention_messages = {
        "customs": {
            "activate": "Your shipment is currently under customs review",
            "release": "Your shipment has been cleared from customs"
        },
        "security": {
            "activate": "Security hold has been placed on your shipment",
            "clear": "Security hold has been cleared from your shipment"
        },
        "damage": {
            "report": "Damage has been reported on your shipment",
            "resolve": "Damage has been resolved on your shipment"
        },
        "return": {
            "initiate": "Return to sender has been initiated for your shipment"
        },
        "delay": {
            "report": "Your shipment has been delayed",
            "resolve": "Delay has been resolved for your shipment"
        }
    }
    
    message = intervention_messages.get(intervention_type, {}).get(action, f"{intervention_type} {action}")
    
    # Create HTML content
    html_content = f"""
    <h2>Shipment Intervention Update</h2>
    <p><strong>Tracking Number:</strong> {shipment.tracking_number}</p>
    <p><strong>Update:</strong> {message}</p>
    """
    
    if kwargs.get('reason'):
        html_content += f"<p><strong>Reason:</strong> {kwargs['reason']}</p>"
    
    if kwargs.get('revised_eta'):
        html_content += f"<p><strong>Revised ETA:</strong> {kwargs['revised_eta']}</p>"
    
    html_content += f"""
    <p><strong>Origin:</strong> {shipment.origin_location}</p>
    <p><strong>Destination:</strong> {shipment.destination_location}</p>
    <p>Track your shipment at: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">https://eukexpress.com/track?number={shipment.tracking_number}</a></p>
    """
    
    # Send to both sender and recipient
    try:
        await email_service.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - {message}",
            html_content=html_content
        )
        
        await email_service.send_email(
            to=[shipment.recipient_email],
            subject=f"Shipment {shipment.tracking_number} - {message}",
            html_content=html_content
        )
        
        return True
    except Exception as e:
        logger.error(f"Failed to send intervention emails: {e}")
        return False

async def send_shipment_created_notification(shipment: Shipment):
    """Send invoice to sender and notification to recipient"""
    logger.info(f"Sending creation notifications for {shipment.tracking_number}")
    
    # Invoice for sender
    invoice_html = f"""
    <h2>Shipment Created Successfully</h2>
    <p>Dear {shipment.sender_name},</p>
    <p>Your shipment has been created successfully.</p>
    <h3>Shipment Details:</h3>
    <ul>
        <li><strong>Tracking Number:</strong> {shipment.tracking_number}</li>
        <li><strong>Invoice Number:</strong> {shipment.invoice_number}</li>
        <li><strong>Origin:</strong> {shipment.origin_location}</li>
        <li><strong>Destination:</strong> {shipment.destination_location}</li>
        <li><strong>Goods:</strong> {shipment.goods_description}</li>
        <li><strong>Weight:</strong> {shipment.weight_kg} kg</li>
        <li><strong>Shipping Amount:</strong> {shipment.declared_currency} {shipment.shipping_amount}</li>
        <li><strong>Sending Date:</strong> {shipment.sending_date}</li>
        <li><strong>Estimated Delivery:</strong> {shipment.estimated_delivery_date}</li>
    </ul>
    <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">https://eukexpress.com/track?number={shipment.tracking_number}</a></p>
    """
    
    # Send invoice to sender
    await email_service.send_email(
        to=[shipment.sender_email],
        subject=f"Invoice for Shipment {shipment.tracking_number}",
        html_content=invoice_html
    )
    
    # Notification for recipient
    notification_html = f"""
    <h2>Shipment Created for You</h2>
    <p>Dear {shipment.recipient_name},</p>
    <p>A shipment has been created for you.</p>
    <h3>Shipment Details:</h3>
    <ul>
        <li><strong>Tracking Number:</strong> {shipment.tracking_number}</li>
        <li><strong>Sender:</strong> {shipment.sender_name}</li>
        <li><strong>Origin:</strong> {shipment.origin_location}</li>
        <li><strong>Destination:</strong> {shipment.destination_location}</li>
        <li><strong>Goods:</strong> {shipment.goods_description}</li>
        <li><strong>Estimated Delivery:</strong> {shipment.estimated_delivery_date}</li>
    </ul>
    <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">https://eukexpress.com/track?number={shipment.tracking_number}</a></p>
    """
    
    await email_service.send_email(
        to=[shipment.recipient_email],
        subject=f"Shipment {shipment.tracking_number} Created for You",
        html_content=notification_html
    )