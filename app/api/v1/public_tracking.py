"""
Public Tracking Endpoints
No authentication required - for customer tracking
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import logging
from datetime import datetime

from app.database import get_db
from app.models import Shipment, StatusHistory
from app.utils.constants import SHIPMENT_STATUSES, STATUS_COLORS
from app.config import settings

router = APIRouter(tags=["Public Tracking"])
logger = logging.getLogger(__name__)

@router.get("/track/{tracking}")
async def public_tracking(
    tracking: str,
    db: Session = Depends(get_db)
):
    """
    Public tracking information - no authentication required
    Returns complete shipment data for customers
    """
    # Find shipment by tracking number
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Tracking number not found")
    
    # Get status timeline
    timeline = db.query(StatusHistory)\
        .filter(StatusHistory.shipment_id == shipment.id)\
        .order_by(StatusHistory.created_at.desc())\
        .all()
    
    # Format timeline for public view
    timeline_data = []
    for event in timeline:
        timeline_data.append({
            "timestamp": event.created_at.isoformat(),
            "event": event.new_status,
            "display": SHIPMENT_STATUSES.get(event.new_status, event.new_status),
            "location": event.location,
            "notes": event.notes,
            "changed_by": event.changed_by
        })
    
    # Check for active interventions
    interventions = {
        "customs_active": shipment.customs_bond_active,
        "security_active": shipment.security_hold_active,
        "damage_reported": shipment.damage_reported,
        "delay_active": shipment.delay_active,
        "return_active": getattr(shipment, 'return_active', False)
    }
    
    # Build image URLs
    front_image_url = None
    rear_image_url = None
    
    if shipment.front_image_path:
        front_image_path = os.path.join(settings.UPLOAD_PATH, "shipments", shipment.tracking_number, os.path.basename(shipment.front_image_path))
        if os.path.exists(front_image_path):
            front_image_url = f"/uploads/shipments/{shipment.tracking_number}/{os.path.basename(shipment.front_image_path)}"
    
    if shipment.rear_image_path:
        rear_image_path = os.path.join(settings.UPLOAD_PATH, "shipments", shipment.tracking_number, os.path.basename(shipment.rear_image_path))
        if os.path.exists(rear_image_path):
            rear_image_url = f"/uploads/shipments/{shipment.tracking_number}/{os.path.basename(shipment.rear_image_path)}"
    
    # Check QR code
    qr_path = os.path.join(settings.QR_CODE_PATH, f"{shipment.tracking_number}.png")
    qr_code_url = f"/qr_codes/{shipment.tracking_number}.png" if os.path.exists(qr_path) else None
    
    # Check invoice PDF
    invoice_url = f"/uploads/invoices/{shipment.tracking_number}.pdf" if shipment.invoice_pdf_path and os.path.exists(shipment.invoice_pdf_path) else None
    
    # Get intervention details
    intervention_details = {
        "customs": {
            "active": shipment.customs_bond_active,
            "activated_at": shipment.customs_bond_activated_at.isoformat() if shipment.customs_bond_activated_at else None,
            "released_at": shipment.customs_bond_released_at.isoformat() if shipment.customs_bond_released_at else None,
            "location": shipment.customs_bond_location,
            "reference": shipment.customs_bond_reference,
            "notes": shipment.customs_bond_notes
        },
        "security": {
            "active": shipment.security_hold_active,
            "activated_at": shipment.security_hold_activated_at.isoformat() if shipment.security_hold_activated_at else None,
            "cleared_at": shipment.security_hold_cleared_at.isoformat() if shipment.security_hold_cleared_at else None,
            "location": shipment.security_hold_location,
            "notes": shipment.security_hold_notes
        },
        "damage": {
            "reported": shipment.damage_reported,
            "reported_at": shipment.damage_reported_at.isoformat() if shipment.damage_reported_at else None,
            "resolved_at": shipment.damage_resolved_at.isoformat() if shipment.damage_resolved_at else None,
            "description": shipment.damage_description,
            "resolution": shipment.damage_resolution_notes
        },
        "return": {
            "active": getattr(shipment, 'return_active', False),
            "initiated_at": shipment.return_initiated_at.isoformat() if hasattr(shipment, 'return_initiated_at') and shipment.return_initiated_at else None,
            "completed_at": shipment.return_completed_at.isoformat() if hasattr(shipment, 'return_completed_at') and shipment.return_completed_at else None,
            "reason": shipment.return_reason if hasattr(shipment, 'return_reason') else None
        },
        "delay": {
            "active": shipment.delay_active,
            "reported_at": shipment.delay_reported_at.isoformat() if shipment.delay_reported_at else None,
            "resolved_at": shipment.delay_resolved_at.isoformat() if shipment.delay_resolved_at else None,
            "reason": shipment.delay_reason,
            "notes": shipment.delay_notes,
            "original_eta": shipment.original_eta.isoformat() if shipment.original_eta else None,
            "revised_eta": shipment.revised_eta.isoformat() if shipment.revised_eta else None
        }
    }
    
    return {
        "tracking": shipment.tracking_number,
        "invoice_number": shipment.invoice_number,
        "status": {
            "current": shipment.current_status,
            "display": SHIPMENT_STATUSES.get(shipment.current_status, shipment.current_status),
            "color": STATUS_COLORS.get(shipment.current_status, "gray"),
            "updated_at": shipment.status_updated_at.isoformat() if shipment.status_updated_at else None
        },
        "route": {
            "origin": shipment.origin_location,
            "origin_code": shipment.origin_code,
            "destination": shipment.destination_location,
            "destination_code": shipment.destination_code,
            "is_international": shipment.is_international
        },
        "sender": {
            "name": shipment.sender_name,
            "email": shipment.sender_email,
            "phone": shipment.sender_phone,
            "address": shipment.sender_address
        },
        "recipient": {
            "name": shipment.recipient_name,
            "email": shipment.recipient_email,
            "phone": shipment.recipient_phone,
            "address": shipment.recipient_address
        },
        "goods": {
            "description": shipment.goods_description,
            "weight": float(shipment.weight_kg) if shipment.weight_kg else None,
            "dimensions": shipment.dimensions,
            "declared_value": float(shipment.declared_value) if shipment.declared_value else None,
            "currency": shipment.declared_currency
        },
        "payment": {
            "shipping_amount": float(shipment.shipping_amount),
            "payment_method": shipment.payment_method,
            "payment_status": shipment.payment_status
        },
        "dates": {
            "sending": shipment.sending_date.isoformat() if shipment.sending_date else None,
            "estimated": shipment.estimated_delivery_date.isoformat() if shipment.estimated_delivery_date else None,
            "actual": shipment.actual_delivery_date.isoformat() if shipment.actual_delivery_date else None
        },
        "images": {
            "front": front_image_url,
            "rear": rear_image_url
        },
        "interventions": interventions,
        "intervention_details": intervention_details,
        "timeline": timeline_data,
        "qr_code": qr_code_url,
        "invoice_pdf": invoice_url,
        "created_at": shipment.created_at.isoformat() if shipment.created_at else None,
        "updated_at": shipment.updated_at.isoformat() if shipment.updated_at else None
    }

@router.get("/track/{tracking}/qr")
async def get_tracking_qr(
    tracking: str,
    db: Session = Depends(get_db)
):
    """
    Get QR code image for tracking
    """
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Tracking number not found")
    
    qr_path = os.path.join(settings.QR_CODE_PATH, f"{shipment.tracking_number}.png")
    
    if not os.path.exists(qr_path):
        raise HTTPException(status_code=404, detail="QR code not found")
    
    return FileResponse(
        qr_path,
        media_type="image/png",
        filename=f"eukexpress-{tracking}-qr.png"
    )

@router.get("/track/{tracking}/invoice")
async def download_invoice(
    tracking: str,
    db: Session = Depends(get_db)
):
    """
    Download invoice PDF
    """
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Tracking number not found")
    
    pdf_path = shipment.invoice_pdf_path
    
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="Invoice PDF not found")
    
    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=f"eukexpress-invoice-{tracking}.pdf"
    )

@router.get("/track/{tracking}/image/{position}")
async def get_shipment_image(
    tracking: str,
    position: str,
    db: Session = Depends(get_db)
):
    """
    Get shipment image (front or rear)
    """
    if position not in ["front", "rear"]:
        raise HTTPException(status_code=400, detail="Position must be 'front' or 'rear'")
    
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Tracking number not found")
    
    image_path = shipment.front_image_path if position == "front" else shipment.rear_image_path
    
    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"{position.capitalize()} image not found")
    
    return FileResponse(
        image_path,
        media_type="image/jpeg",
        filename=f"{shipment.tracking_number}_{position}.jpg"
    )

@router.get("/status")
async def public_status():
    """
    Public status endpoint for keep-alive pings
    """
    return {
        "status": "operational",
        "service": "EukExpress Public Tracking",
        "timestamp": datetime.utcnow().isoformat()
    }

# Export router
public_router = router