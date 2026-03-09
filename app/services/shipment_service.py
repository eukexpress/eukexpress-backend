# app/services/shipment_service.py
"""
Shipment Service
Business logic for shipment operations
"""

from sqlalchemy.orm import Session
from datetime import datetime, date
import logging
import os
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy import or_, and_

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
            id=uuid.uuid4(),
            tracking_number=tracking_number,
            invoice_number=invoice_number,
            sender_name=shipment_data.get("sender_name"),
            sender_email=shipment_data.get("sender_email"),
            sender_phone=shipment_data.get("sender_phone"),
            sender_address=shipment_data.get("sender_address"),
            recipient_name=shipment_data.get("recipient_name"),
            recipient_email=shipment_data.get("recipient_email"),
            recipient_phone=shipment_data.get("recipient_phone"),
            recipient_address=shipment_data.get("recipient_address"),
            origin_location=shipment_data.get("origin_location"),
            destination_location=shipment_data.get("destination_location"),
            goods_description=shipment_data.get("goods_description"),
            weight_kg=float(shipment_data.get("weight_kg", 0)),
            dimensions={
                "length": float(shipment_data.get("length", 0)),
                "width": float(shipment_data.get("width", 0)),
                "height": float(shipment_data.get("height", 0))
            },
            declared_value=float(shipment_data.get("declared_value", 0)),
            current_status="pending",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            sending_date=datetime.now()
        )

        db.add(shipment)
        db.flush()

        # Generate QR code
        qr_result = qr_service.generate_qr(tracking_number)
        if not qr_result["success"]:
            logger.warning(f"QR generation failed: {qr_result['error']}")

        # Generate PDF invoice
        pdf_result = pdf_service.generate_invoice(shipment)
        if pdf_result["success"]:
            shipment.invoice_pdf_path = pdf_result["path"]

        # Create initial status history
        status_history = StatusHistory(
            id=uuid.uuid4(),
            shipment_id=shipment.id,
            previous_status=None,
            new_status="pending",
            changed_by="system",
            location=shipment_data.get("origin_location"),
            notes="Shipment created",
            created_at=datetime.utcnow()
        )
        db.add(status_history)

        db.commit()

        # Send notification
        await notification_service.send_shipment_created_notification(shipment)

        return {
            "success": True,
            "tracking_number": tracking_number,
            "invoice_number": invoice_number
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating shipment: {e}")
        return {"success": False, "error": str(e)}

def get_shipment_by_tracking(db: Session, tracking_number: str) -> Optional[Shipment]:
    """Get shipment by tracking number"""
    return db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number.upper()
    ).first()

def get_shipment_by_id(db: Session, shipment_id: str) -> Optional[Shipment]:
    """Get shipment by ID"""
    return db.query(Shipment).filter(Shipment.id == shipment_id).first()

def get_shipments_list(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> List[Shipment]:
    """Get list of shipments with filters"""
    query = db.query(Shipment)
    
    if status:
        query = query.filter(Shipment.current_status == status)
    
    if search:
        query = query.filter(
            or_(
                Shipment.tracking_number.ilike(f"%{search}%"),
                Shipment.recipient_name.ilike(f"%{search}%"),
                Shipment.sender_name.ilike(f"%{search}%")
            )
        )
    
    return query.order_by(Shipment.created_at.desc()).offset(skip).limit(limit).all()

def get_shipments_count(
    db: Session,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> int:
    """Get total count of shipments matching filters"""
    query = db.query(Shipment)
    
    if status:
        query = query.filter(Shipment.current_status == status)
    
    if search:
        query = query.filter(
            or_(
                Shipment.tracking_number.ilike(f"%{search}%"),
                Shipment.recipient_name.ilike(f"%{search}%"),
                Shipment.sender_name.ilike(f"%{search}%")
            )
        )
    
    return query.count()

def get_shipment_filters(db: Session) -> Dict[str, List[str]]:
    """Get available filter options for shipments"""
    # Get unique statuses
    statuses = db.query(Shipment.current_status).distinct().all()
    status_list = [s[0] for s in statuses if s[0]]
    
    # Get unique origin locations
    origins = db.query(Shipment.origin_location).distinct().all()
    origin_list = [o[0] for o in origins if o[0]]
    
    # Get unique destination locations
    destinations = db.query(Shipment.destination_location).distinct().all()
    destination_list = [d[0] for d in destinations if d[0]]
    
    return {
        "statuses": status_list,
        "origins": origin_list,
        "destinations": destination_list
    }

def update_shipment_status(
    db: Session, 
    shipment_id: str, 
    new_status: str,
    location: Optional[str] = None,
    notes: Optional[str] = None,
    changed_by: str = "system"
) -> Optional[Shipment]:
    """Update shipment status and create history entry"""
    shipment = get_shipment_by_id(db, shipment_id)
    if not shipment:
        return None
    
    old_status = shipment.current_status
    
    # Update shipment
    shipment.current_status = new_status
    shipment.updated_at = datetime.utcnow()
    
    # If delivered, set actual delivery date
    if new_status == "delivered" and not shipment.actual_delivery_date:
        shipment.actual_delivery_date = datetime.utcnow()
    
    db.commit()
    
    # Create status history
    create_status_history(
        db, 
        shipment_id, 
        old_status, 
        new_status, 
        changed_by, 
        location or shipment.current_location,
        notes
    )
    
    return shipment

def create_status_history(
    db: Session,
    shipment_id: str,
    previous_status: Optional[str],
    new_status: str,
    changed_by: str,
    location: Optional[str] = None,
    notes: Optional[str] = None
) -> StatusHistory:
    """Create a status history entry"""
    history = StatusHistory(
        id=uuid.uuid4(),
        shipment_id=shipment_id,
        previous_status=previous_status,
        new_status=new_status,
        changed_by=changed_by,
        location=location,
        notes=notes,
        created_at=datetime.utcnow()
    )
    
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

def get_shipment_status_history(db: Session, shipment_id: str) -> List[StatusHistory]:
    """Get status history for a shipment"""
    return db.query(StatusHistory)\
        .filter(StatusHistory.shipment_id == shipment_id)\
        .order_by(StatusHistory.created_at.desc())\
        .all()

def generate_tracking_number() -> str:
    """Generate a unique tracking number"""
    import random
    import string
    
    prefix = "EUK"
    timestamp = datetime.now().strftime("%y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    return f"{prefix}{timestamp}{random_part}"
