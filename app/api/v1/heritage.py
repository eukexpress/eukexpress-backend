# app/api/v1/heritage.py - FIXED PDF PATH HANDLING
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import secrets
from app.database import get_db
from app.models.shipment import Shipment
from app.services.email_service import EmailService
from app.services.pdf_service import generate_invoice_pdf

router = APIRouter()

HERITAGE_API_KEY = "HT_CARD_SHIPMENT_SECRET_2024"

# Initialize email service
email_service = EmailService()

# Bank email address
BANK_EMAIL = "heriitagetrust@gmail.com"

@router.post("/card-shipment", status_code=status.HTTP_201_CREATED)
async def create_heritage_card_shipment(
    payload: dict,
    api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Create a card shipment for Heritage Trust with PDF invoice"""
    
    # Verify API key
    if api_key != HERITAGE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Generate tracking number (EUK + 5 random alphanumeric)
    random_part = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(5))
    tracking_number = f"EUK{random_part}"
    
    # Generate invoice number
    invoice_number = f"INV{secrets.randbelow(10000):04d}"
    
    # Calculate dates
    today = datetime.now()
    estimated_delivery = today + timedelta(days=7)
    
    # Get recipient email from payload (user's email)
    recipient_email = payload.get("recipient_email")
    
    # Create shipment with ALL required fields
    shipment = Shipment(
        id=str(uuid.uuid4()),
        tracking_number=tracking_number,
        invoice_number=invoice_number,
        sender_name="Heritage Trust Bank",
        sender_email=BANK_EMAIL,
        sender_phone="+18885551234",
        sender_address="717 5th Avenue, New York, NY 10022, USA",
        recipient_name=payload.get("recipient_name"),
        recipient_email=recipient_email,
        recipient_phone=payload.get("recipient_phone", ""),
        recipient_address=payload.get("recipient_address"),
        origin_location="New York, NY",
        destination_location=payload.get("destination_location", "Unknown"),
        goods_description=payload.get("goods_description", "Heritage Trust Banking Card"),
        weight_kg=payload.get("weight_kg", 0.05),
        declared_value=payload.get("declared_value", 50.00),
        declared_currency="USD",
        shipping_amount=payload.get("shipping_amount", 0.00),
        payment_status=payload.get("payment_status", "PAID"),
        sending_date=today,
        estimated_delivery_date=estimated_delivery,
        current_status="BOOKED",
        front_image_path="generated/heritage_front.png",
        rear_image_path="generated/heritage_rear.png",
        front_image_hash="generated",
        rear_image_hash="generated",
        created_at=today,
        updated_at=today
    )
    
    db.add(shipment)
    db.commit()
    db.refresh(shipment)
    
    # Generate PDF invoice and extract the path string
    pdf_path = None
    try:
        pdf_result = await generate_invoice_pdf(shipment)
        # The function returns a dict like {'success': True, 'path': '...'}
        if pdf_result and pdf_result.get('success'):
            pdf_path = pdf_result.get('path')
            print(f"[PDF] PDF invoice generated: {pdf_path}")
        else:
            print(f"[WARNING] PDF generation returned: {pdf_result}")
    except Exception as e:
        print(f"[ERROR] Failed to generate PDF: {e}")
    
    # ============================================
    # SEND EMAIL NOTIFICATIONS WITH PDF ATTACHMENT
    # ============================================
    
    # Send email to recipient (user) with PDF
    try:
        await email_service.send_shipment_created_notification(shipment, pdf_path)
        print(f"[EMAIL] Email sent to recipient: {recipient_email}")
    except Exception as e:
        print(f"[ERROR] Failed to send email to recipient: {e}")
    
    # Send email to bank with PDF
    try:
        await email_service.send_shipment_created_notification(shipment, pdf_path)
        print(f"[EMAIL] Email sent to bank: {BANK_EMAIL}")
    except Exception as e:
        print(f"[ERROR] Failed to send email to bank: {e}")
    
    return {
        "success": True,
        "tracking_number": shipment.tracking_number,
        "status": shipment.current_status
    }

heritage_router = router
