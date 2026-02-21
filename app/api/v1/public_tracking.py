# Eukexpress\backend\app\api\v1\public_tracking.py
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

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/track/{tracking}")
async def public_tracking(
    tracking: str,
    db: Session = Depends(get_db)
):
    """
    Public tracking information - no authentication required
    Returns limited shipment data for customers
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
            "location": event.location
        })
    
    # Check for active interventions (public view)
    interventions = {
        "customs_active": shipment.customs_bond_active,
        "security_active": shipment.security_hold_active,
        "damage_reported": shipment.damage_reported,
        "delay_active": shipment.delay_active
    }
    
    # Build image URLs
    front_image_path = os.path.join(settings.UPLOAD_PATH, "shipments", shipment.tracking_number, "front.jpg")
    rear_image_path = os.path.join(settings.UPLOAD_PATH, "shipments", shipment.tracking_number, "rear.jpg")
    
    front_image_url = f"/uploads/shipments/{shipment.tracking_number}/front.jpg" if os.path.exists(front_image_path) else None
    rear_image_url = f"/uploads/shipments/{shipment.tracking_number}/rear.jpg" if os.path.exists(rear_image_path) else None
    
    # Check QR code
    qr_path = os.path.join(settings.QR_CODE_PATH, f"{shipment.tracking_number}.png")
    
    return {
        "tracking": shipment.tracking_number,
        "status": {
            "current": shipment.current_status,
            "display": SHIPMENT_STATUSES.get(shipment.current_status, shipment.current_status),
            "color": STATUS_COLORS.get(shipment.current_status, "gray")
        },
        "route": {
            "origin": shipment.origin_location,
            "destination": shipment.destination_location
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
        "timeline": timeline_data,
        "qr_code": f"/qr_codes/{shipment.tracking_number}.png" if os.path.exists(qr_path) else None
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