# Eukexpress\backend\app\api\v1\communication.py
"""
Communication Endpoints
Direct messaging and email management
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging
from datetime import datetime

from app.database import get_db
from app.models import Shipment, EmailLog
from app.schemas.email import DirectMessage, EmailResend
from app.api.v1.auth import oauth2_scheme
from app.services import auth_service, email_service
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{tracking}/message")
async def send_direct_message(
    tracking: str,
    message: DirectMessage,
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Send direct message to sender or recipient"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Find shipment
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Prepare email content
    tracking_link = f"{settings.APP_URL}/track?number={shipment.tracking_number}" if message.include_tracking_link else None
    
    # Determine recipients
    recipients = []
    if message.recipient in ["sender", "both"]:
        recipients.append(("sender", shipment.sender_email, shipment.sender_name))
    if message.recipient in ["recipient", "both"]:
        recipients.append(("recipient", shipment.recipient_email, shipment.recipient_name))
    
    sent_to = []
    
    # Send emails
    for recipient_type, email, name in recipients:
        # Render custom message template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset='UTF-8'>
            <title>Message from EukExpress</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #003366; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                .tracking-link {{ background: #003366; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; }}
            </style>
        </head>
        <body>
            <div class='container'>
                <div class='header'>
                    <h1>EukExpress Global Logistics</h1>
                </div>
                <div class='content'>
                    <h2>Message regarding shipment {shipment.tracking_number}</h2>
                    <p>Dear {name},</p>
                    <div style="background: white; padding: 15px; border-left: 4px solid #003366; margin: 20px 0;">
                        {message.message}
                    </div>
                    {f'<p><a href="{tracking_link}" class="tracking-link">Track Your Shipment</a></p>' if tracking_link else ''}
                </div>
                <div class='footer'>
                    <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
                    <p>This is an automated message, please do not reply directly.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send in background
        background_tasks.add_task(
            email_service.send_email,
            to_email=email,
            subject=message.subject,
            html_content=html_content,
            shipment_id=shipment.id,
            recipient_type=recipient_type,
            email_type="custom_message"
        )
        sent_to.append(email)
    
    logger.info(f"Direct message sent for {tracking} to {len(sent_to)} recipients")
    
    return {
        "success": True,
        "message": "Message sent successfully",
        "sent_to": sent_to,
        "recipient_count": len(sent_to)
    }

@router.post("/{tracking}/email/resend")
async def resend_email(
    tracking: str,
    email_data: EmailResend,
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Resend specific email"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Find shipment
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Resend based on type
    if email_data.email_type == "invoice":
        background_tasks.add_task(email_service.send_invoice, shipment, db)
        email_type_sent = "invoice"
    elif email_data.email_type == "last_notification":
        # Get last email sent
        last_email = db.query(EmailLog)\
            .filter(EmailLog.shipment_id == shipment.id)\
            .order_by(desc(EmailLog.created_at))\
            .first()
        
        if not last_email:
            raise HTTPException(status_code=404, detail="No previous email found")
        
        # Resend based on type
        if last_email.email_type == "invoice":
            background_tasks.add_task(email_service.send_invoice, shipment, db)
        elif last_email.email_type == "customs_bond":
            background_tasks.add_task(email_service.send_customs_bond_notification, shipment, db)
        elif last_email.email_type == "delivery_confirmation":
            background_tasks.add_task(email_service.send_delivery_confirmation, shipment, db)
        # Add other types as needed
        
        email_type_sent = last_email.email_type
    
    logger.info(f"Email resent for {tracking}: {email_type_sent}")
    
    return {
        "success": True,
        "message": f"{email_type_sent} email resent successfully",
        "email_type": email_type_sent
    }

@router.get("/{tracking}/email-history", response_model=list)
async def get_email_history(
    tracking: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get email history for shipment"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Find shipment
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Get email history
    emails = db.query(EmailLog)\
        .filter(EmailLog.shipment_id == shipment.id)\
        .order_by(desc(EmailLog.created_at))\
        .all()
    
    history = []
    for email in emails:
        history.append({
            "timestamp": email.created_at.isoformat(),
            "type": email.email_type,
            "recipient": email.recipient_type,
            "recipient_email": email.recipient_email,
            "subject": email.subject,
            "status": email.status,
            "message_id": email.message_id
        })
    
    return history