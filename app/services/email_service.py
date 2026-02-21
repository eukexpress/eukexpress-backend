# Eukexpress\backend\app\services\email_service.py
"""
Email Service - Resend API Integration
Handles all email communications with templates
"""

import logging
import resend
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from sqlalchemy.orm import Session

from app.config import settings
from app.models import EmailLog, Shipment
from app.services import pdf_service, qr_service

# Configure Resend
resend.api_key = settings.RESEND_API_KEY

# Configure Jinja2 template environment
template_env = Environment(
    loader=FileSystemLoader("app/templates/email"),
    autoescape=True
)

logger = logging.getLogger(__name__)

async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    shipment_id: str = None,
    recipient_type: str = None,
    email_type: str = None,
    attachments: list = None
):
    """
    Base email sending function using Resend
    """
    try:
        params = {
            "from": f"{settings.RESEND_FROM_NAME} <{settings.RESEND_FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        if attachments:
            params["attachments"] = attachments
        
        # Send via Resend
        response = resend.Emails.send(params)
        
        # Log the email
        if shipment_id and email_type:
            log_email(
                shipment_id=shipment_id,
                recipient_type=recipient_type,
                recipient_email=to_email,
                email_type=email_type,
                subject=subject,
                message_id=response.get('id'),
                status='SENT'
            )
        
        logger.info(f"Email sent to {to_email}: {subject}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        
        # Log failure
        if shipment_id and email_type:
            log_email(
                shipment_id=shipment_id,
                recipient_type=recipient_type,
                recipient_email=to_email,
                email_type=email_type,
                subject=subject,
                status='FAILED'
            )
        raise e

def log_email(shipment_id, recipient_type, recipient_email, email_type, subject, message_id=None, status='SENT'):
    """Log email to database"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        email_log = EmailLog(
            shipment_id=shipment_id,
            recipient_type=recipient_type,
            recipient_email=recipient_email,
            email_type=email_type,
            subject=subject,
            message_id=message_id,
            status=status
        )
        db.add(email_log)
        db.commit()
    except Exception as e:
        logger.error(f"Failed to log email: {e}")
    finally:
        db.close()

async def send_invoice(shipment: Shipment, db: Session):
    """Send invoice email with PDF attachment"""
    # Generate invoice PDF
    pdf_path = await pdf_service.generate_invoice_pdf(shipment)
    
    # Generate QR code
    qr_path = await qr_service.generate_qr_code(shipment.tracking_number)
    
    # Render template
    template = template_env.get_template("invoice.html")
    html_content = template.render(
        tracking=shipment.tracking_number,
        recipient_name=shipment.recipient_name,
        sender_name=shipment.sender_name,
        origin=shipment.origin_location,
        destination=shipment.destination_location,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    # Prepare attachments
    attachments = []
    if pdf_path:
        with open(pdf_path, 'rb') as f:
            attachments.append({
                "filename": f"invoice-{shipment.tracking_number}.pdf",
                "content": list(f.read())
            })
    
    if qr_path:
        with open(qr_path, 'rb') as f:
            attachments.append({
                "filename": f"qr-{shipment.tracking_number}.png",
                "content": list(f.read())
            })
    
    # Send to recipient
    await send_email(
        to_email=shipment.recipient_email,
        subject=f"Invoice for Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="recipient",
        email_type="invoice",
        attachments=attachments
    )
    
    # Also send to sender if different
    if shipment.sender_email != shipment.recipient_email:
        await send_email(
            to_email=shipment.sender_email,
            subject=f"Invoice for Shipment {shipment.tracking_number}",
            html_content=html_content,
            shipment_id=shipment.id,
            recipient_type="sender",
            email_type="invoice",
            attachments=attachments
        )

async def send_customs_bond_notification(shipment: Shipment, db: Session):
    """Send customs bond notification"""
    template = template_env.get_template("customs_bond.html")
    html_content = template.render(
        tracking=shipment.tracking_number,
        recipient_name=shipment.recipient_name,
        location=shipment.customs_bond_location,
        reference=shipment.customs_bond_reference,
        date=datetime.now().strftime("%Y-%m-%d"),
        tracking_link=f"{settings.APP_URL}/track?number={shipment.tracking_number}"
    )
    
    await send_email(
        to_email=shipment.recipient_email,
        subject=f"Customs Bond Held - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="recipient",
        email_type="customs_bond"
    )

async def send_customs_released_notification(shipment: Shipment, duration, db: Session):
    """Send customs clearance notification"""
    template = template_env.get_template("customs_released.html")
    duration_text = str(duration).split('.')[0] if duration else "processed"
    
    html_content = template.render(
        tracking=shipment.tracking_number,
        recipient_name=shipment.recipient_name,
        duration=duration_text,
        date=datetime.now().strftime("%Y-%m-%d"),
        tracking_link=f"{settings.APP_URL}/track?number={shipment.tracking_number}"
    )
    
    await send_email(
        to_email=shipment.recipient_email,
        subject=f"Customs Cleared - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="recipient",
        email_type="customs_released"
    )

async def send_security_hold_notification(shipment: Shipment, db: Session):
    """Send security hold notification"""
    template = template_env.get_template("security_hold.html")
    html_content = template.render(
        tracking=shipment.tracking_number,
        recipient_name=shipment.recipient_name,
        location=shipment.security_hold_location,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    await send_email(
        to_email=shipment.recipient_email,
        subject=f"Security Hold - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="recipient",
        email_type="security_hold"
    )

async def send_security_cleared_notification(shipment: Shipment, db: Session):
    """Send security cleared notification"""
    template = template_env.get_template("security_cleared.html")
    html_content = template.render(
        tracking=shipment.tracking_number,
        recipient_name=shipment.recipient_name,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    await send_email(
        to_email=shipment.recipient_email,
        subject=f"Security Cleared - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="recipient",
        email_type="security_cleared"
    )

async def send_damage_report_notification(shipment: Shipment, db: Session):
    """Send damage report notification to both parties"""
    template = template_env.get_template("damage_report.html")
    html_content = template.render(
        tracking=shipment.tracking_number,
        recipient_name=shipment.recipient_name,
        sender_name=shipment.sender_name,
        description=shipment.damage_description,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    # Send to recipient
    await send_email(
        to_email=shipment.recipient_email,
        subject=f"Damage Reported - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="recipient",
        email_type="damage_report"
    )
    
    # Send to sender
    await send_email(
        to_email=shipment.sender_email,
        subject=f"Damage Reported - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="sender",
        email_type="damage_report"
    )

async def send_damage_resolved_notification(shipment: Shipment, db: Session):
    """Send damage resolved notification"""
    template = template_env.get_template("damage_resolved.html")
    html_content = template.render(
        tracking=shipment.tracking_number,
        recipient_name=shipment.recipient_name,
        resolution=shipment.damage_resolution_notes,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    await send_email(
        to_email=shipment.recipient_email,
        subject=f"Damage Resolved - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="recipient",
        email_type="damage_resolved"
    )

async def send_return_notification(shipment: Shipment, db: Session):
    """Send return to sender notification"""
    template = template_env.get_template("return_notification.html")
    html_content = template.render(
        tracking=shipment.tracking_number,
        recipient_name=shipment.recipient_name,
        sender_name=shipment.sender_name,
        reason=shipment.return_reason,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    # Send to recipient
    await send_email(
        to_email=shipment.recipient_email,
        subject=f"Return Initiated - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="recipient",
        email_type="return_initiated"
    )
    
    # Send to sender
    await send_email(
        to_email=shipment.sender_email,
        subject=f"Return Initiated - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="sender",
        email_type="return_initiated"
    )

async def send_delay_notification(shipment: Shipment, reason: str, revised_eta, db: Session):
    """Send delay notification"""
    template = template_env.get_template("delay_notification.html")
    html_content = template.render(
        tracking=shipment.tracking_number,
        recipient_name=shipment.recipient_name,
        reason=reason,
        original_eta=shipment.estimated_delivery_date.strftime("%Y-%m-%d"),
        revised_eta=revised_eta.strftime("%Y-%m-%d") if revised_eta else "To be determined",
        date=datetime.now().strftime("%Y-%m-%d")
    )
    
    await send_email(
        to_email=shipment.recipient_email,
        subject=f"Delay Notification - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="recipient",
        email_type="delay_notification"
    )

async def send_delivery_confirmation(shipment: Shipment, db: Session):
    """Send delivery confirmation to both parties"""
    template = template_env.get_template("delivery_confirmation.html")
    html_content = template.render(
        tracking=shipment.tracking_number,
        recipient_name=shipment.recipient_name,
        sender_name=shipment.sender_name,
        delivery_date=shipment.actual_delivery_date.strftime("%Y-%m-%d") if shipment.actual_delivery_date else datetime.now().strftime("%Y-%m-%d"),
        destination=shipment.destination_location
    )
    
    # Send to recipient
    await send_email(
        to_email=shipment.recipient_email,
        subject=f"Delivery Confirmed - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="recipient",
        email_type="delivery_confirmation"
    )
    
    # Send to sender
    await send_email(
        to_email=shipment.sender_email,
        subject=f"Delivery Confirmed - Shipment {shipment.tracking_number}",
        html_content=html_content,
        shipment_id=shipment.id,
        recipient_type="sender",
        email_type="delivery_confirmation"
    )