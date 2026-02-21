# Eukexpress\backend\app\services\shipment_service.py
"""
Shipment Service
Business logic for shipment operations
"""

from sqlalchemy.orm import Session
from datetime import datetime, date
import logging
import os
import uuid

from app.models import Shipment, StatusHistory
from app.services import tracking_service, image_service, qr_service, pdf_service, notification_service
from app.utils.constants import SHIPMENT_STATUSES

logger = logging.getLogger(__name__)

async def create_shipment(db: Session, shipment_data: dict, front_image, rear_image):
    """Create a new shipment with all necessary processing"""
    try:
        # Generate tracking number
        tracking_number = tracking_service.generate_unique_tracking(db)
        
        # Generate invoice number
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{tracking_number[-5:]}"
        
        # Validate and save images
        front_result = await image_service.save_image(front_image, tracking_number, "front")
        rear_result = await image_service.save_image(rear_image, tracking_number, "rear")
        
        if not front_result["success"] or not rear_result["success"]:
            return {"success": False, "error": "Image validation failed"}
        
        # Check for duplicate images
        if front_result["hash"] == rear_result["hash"]:
            return {"success": False, "error": "Front and rear images are identical"}
        
        # Create shipment record
        shipment = Shipment(
            tracking_number=tracking_number,
            invoice_number=invoice_number,
            sender_name=shipment_data["sender_name"],
            sender_email=shipment_data["sender_email"],
            sender_phone=shipment_data["sender_phone"],
            sender_address=shipment_data["sender_address"],
            recipient_name=shipment_data["recipient_name"],
            recipient_email=shipment_data["recipient_email"],
            recipient_phone=shipment_data["recipient_phone"],
            recipient_address=shipment_data["recipient_address"],
            origin_location=shipment_data["origin_location"],
            destination_location=shipment_data["destination_location"],
            goods_description=shipment_data["goods_description"],
            weight_kg=shipment_data.get("weight_kg"),
            dimensions=shipment_data.get("dimensions"),
            declared_value=shipment_data.get("declared_value"),
            shipping_amount=shipment_data["shipping_amount"],
            payment_method=shipment_data.get("payment_method"),
            payment_status=shipment_data.get("payment_status", "PENDING"),
            sending_date=shipment_data["sending_date"],
            estimated_delivery_date=shipment_data["estimated_delivery_date"],
            front_image_path=front_result["path"],
            rear_image_path=rear_result["path"],
            front_image_hash=front_result["hash"],
            rear_image_hash=rear_result["hash"],
            is_international=shipment_data.get("is_international", False)
        )
        
        db.add(shipment)
        db.flush()  # Get ID without committing
        
        # Create initial status history
        status_history = StatusHistory(
            shipment_id=shipment.id,
            previous_status=None,
            new_status="BOOKED",
            changed_by="admin",
            location=shipment.origin_location,
            notes="Shipment created"
        )
        db.add(status_history)
        
        # Generate QR code
        qr_path = await qr_service.generate_qr_code(tracking_number)
        if qr_path:
            shipment.qr_code_path = qr_path
        
        # Generate invoice PDF (in background ideally)
        pdf_path = await pdf_service.generate_invoice_pdf(shipment)
        if pdf_path:
            shipment.invoice_pdf_path = pdf_path
        
        db.commit()
        
        # Send invoice email
        await notification_service.trigger_status_change_notifications(
            shipment, None, "BOOKED", db
        )
        
        logger.info(f"Shipment created: {tracking_number}")
        
        return {
            "success": True,
            "tracking_number": tracking_number,
            "invoice_number": invoice_number,
            "qr_code_url": f"/qr_codes/{tracking_number}.png",
            "invoice_pdf_url": f"/uploads/invoices/invoice-{tracking_number}.pdf",
            "message": "Shipment created successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to create shipment: {e}")
        db.rollback()
        return {"success": False, "error": str(e)}

def get_shipment_by_tracking(db: Session, tracking_number: str):
    """Get shipment by tracking number"""
    return db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number.upper()
    ).first()

def update_shipment_status(db: Session, shipment_id: uuid.UUID, new_status: str, location: str = None, notes: str = None):
    """Update shipment status and create history entry"""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        return None
    
    old_status = shipment.current_status
    
    # Update shipment
    shipment.current_status = new_status
    shipment.status_updated_at = datetime.utcnow()
    if location:
        shipment.current_location = location
    
    # Create history entry
    history = StatusHistory(
        shipment_id=shipment_id,
        previous_status=old_status,
        new_status=new_status,
        changed_by="admin",
        location=location,
        notes=notes
    )
    db.add(history)
    db.commit()
    
    return shipment