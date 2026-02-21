# Eukexpress\backend\app\api\v1\shipment_detail.py
"""
Layer 3: Shipment Operations Endpoints
Complete control for a single shipment
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging
from datetime import datetime

from app.database import get_db
from app.models import Shipment, StatusHistory, EmailLog, InterventionLog
from app.schemas.shipment import ShipmentResponse, StatusUpdate
from app.api.v1.auth import oauth2_scheme
from app.services import auth_service, tracking_service, notification_service
from app.utils.constants import SHIPMENT_STATUSES, STATUS_COLORS

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{tracking}", response_model=dict)
async def get_shipment_detail(
    tracking: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Get complete shipment details for operations
    Layer 3: Shipment Operations
    """
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
    
    # Get status timeline
    timeline = db.query(StatusHistory)\
        .filter(StatusHistory.shipment_id == shipment.id)\
        .order_by(desc(StatusHistory.created_at))\
        .all()
    
    timeline_data = []
    for event in timeline:
        timeline_data.append({
            "timestamp": event.created_at.isoformat(),
            "event": f"{event.previous_status or 'START'} → {event.new_status}",
            "display": SHIPMENT_STATUSES.get(event.new_status, event.new_status),
            "location": event.location,
            "notes": event.notes,
            "type": "status"
        })
    
    # Get email history
    email_history = db.query(EmailLog)\
        .filter(EmailLog.shipment_id == shipment.id)\
        .order_by(desc(EmailLog.created_at))\
        .all()
    
    email_data = []
    for email in email_history:
        email_data.append({
            "timestamp": email.created_at.isoformat(),
            "type": email.email_type,
            "recipient": email.recipient_type,
            "recipient_email": email.recipient_email,
            "subject": email.subject,
            "status": email.status
        })
    
    # Calculate intervention durations
    interventions = {
        "customs": {
            "active": shipment.customs_bond_active,
            "activated_at": shipment.customs_bond_activated_at.isoformat() if shipment.customs_bond_activated_at else None,
            "released_at": shipment.customs_bond_released_at.isoformat() if shipment.customs_bond_released_at else None,
            "location": shipment.customs_bond_location,
            "reference": shipment.customs_bond_reference,
            "notes": shipment.customs_bond_notes,
            "duration": _calculate_duration(
                shipment.customs_bond_activated_at,
                shipment.customs_bond_released_at
            ) if shipment.customs_bond_activated_at else None
        },
        "security": {
            "active": shipment.security_hold_active,
            "activated_at": shipment.security_hold_activated_at.isoformat() if shipment.security_hold_activated_at else None,
            "cleared_at": shipment.security_hold_cleared_at.isoformat() if shipment.security_hold_cleared_at else None,
            "location": shipment.security_hold_location,
            "notes": shipment.security_hold_notes,
            "duration": _calculate_duration(
                shipment.security_hold_activated_at,
                shipment.security_hold_cleared_at
            ) if shipment.security_hold_activated_at else None
        },
        "damage": {
            "reported": shipment.damage_reported,
            "reported_at": shipment.damage_reported_at.isoformat() if shipment.damage_reported_at else None,
            "resolved_at": shipment.damage_resolved_at.isoformat() if shipment.damage_resolved_at else None,
            "description": shipment.damage_description,
            "resolution": shipment.damage_resolution_notes,
            "duration": _calculate_duration(
                shipment.damage_reported_at,
                shipment.damage_resolved_at
            ) if shipment.damage_reported_at else None
        },
        "return": {
            "active": shipment.return_active,
            "initiated_at": shipment.return_initiated_at.isoformat() if shipment.return_initiated_at else None,
            "completed_at": shipment.return_completed_at.isoformat() if shipment.return_completed_at else None,
            "reason": shipment.return_reason
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
        "route": {
            "origin": shipment.origin_location,
            "origin_code": shipment.origin_code,
            "destination": shipment.destination_location,
            "destination_code": shipment.destination_code,
            "is_international": shipment.is_international
        },
        "commodity": {
            "description": shipment.goods_description,
            "weight": float(shipment.weight_kg) if shipment.weight_kg else None,
            "dimensions": shipment.dimensions,
            "declared_value": float(shipment.declared_value) if shipment.declared_value else None,
            "currency": shipment.declared_currency
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
        "images": {
            "front": f"/uploads/shipments/{shipment.tracking_number}/front.jpg",
            "rear": f"/uploads/shipments/{shipment.tracking_number}/rear.jpg"
        },
        "payment": {
            "amount": float(shipment.shipping_amount),
            "currency": shipment.payment_currency,
            "method": shipment.payment_method,
            "status": shipment.payment_status,
            "received_at": shipment.payment_received_at.isoformat() if shipment.payment_received_at else None
        },
        "status": {
            "current": shipment.current_status,
            "display": SHIPMENT_STATUSES.get(shipment.current_status, shipment.current_status),
            "color": STATUS_COLORS.get(shipment.current_status, "gray"),
            "started_at": shipment.status_updated_at.isoformat(),
            "estimated_delivery": shipment.estimated_delivery_date.isoformat(),
            "actual_delivery": shipment.actual_delivery_date.isoformat() if shipment.actual_delivery_date else None,
            "current_location": shipment.current_location
        },
        "interventions": interventions,
        "timeline": timeline_data,
        "communication": {
            "email_history": email_data
        },
        "qr_code": f"/qr_codes/{shipment.tracking_number}.png",
        "invoice_pdf": f"/invoices/{shipment.tracking_number}.pdf" if shipment.invoice_pdf_path else None,
        "created_at": shipment.created_at.isoformat(),
        "updated_at": shipment.updated_at.isoformat()
    }

@router.post("/{tracking}/status")
async def update_shipment_status(
    tracking: str,
    status_update: StatusUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Update shipment status progression
    """
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
    
    # Validate status transition
    old_status = shipment.current_status
    new_status = status_update.status
    
    # Update shipment
    shipment.current_status = new_status
    shipment.status_updated_at = datetime.utcnow()
    if status_update.location:
        shipment.current_location = status_update.location
    
    # If delivered, set actual delivery date
    if new_status == "DELIVERED" and not shipment.actual_delivery_date:
        shipment.actual_delivery_date = datetime.utcnow().date()
    
    db.commit()
    
    # Create status history entry
    from app.models import StatusHistory
    history_entry = StatusHistory(
        shipment_id=shipment.id,
        previous_status=old_status,
        new_status=new_status,
        changed_by="admin",
        location=status_update.location,
        notes=status_update.notes
    )
    db.add(history_entry)
    db.commit()
    
    # Trigger notifications
    await notification_service.trigger_status_change_notifications(
        shipment, old_status, new_status, db
    )
    
    logger.info(f"Shipment {tracking} status updated: {old_status} -> {new_status}")
    
    return {
        "success": True,
        "new_status": new_status,
        "old_status": old_status,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/{tracking}/available-statuses")
async def get_available_statuses(
    tracking: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Get next available statuses based on current status
    """
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
    
    # Define status flow based on current status
    status_flow = {
        "BOOKED": ["COLLECTED"],
        "COLLECTED": ["WAREHOUSE_PROCESSING"],
        "WAREHOUSE_PROCESSING": ["TERMINAL_ARRIVAL"],
        "TERMINAL_ARRIVAL": ["EN_ROUTE"],
        "EN_ROUTE": ["CUSTOMS_BOND", "SECURITY_HOLD", "TRANSIT_EXCEPTION", "DESTINATION_HUB"],
        "CUSTOMS_BOND": ["CUSTOMS_CLEARED"],
        "CUSTOMS_CLEARED": ["EN_ROUTE", "DESTINATION_HUB"],
        "SECURITY_HOLD": ["SECURITY_CLEARED"],
        "SECURITY_CLEARED": ["EN_ROUTE", "DESTINATION_HUB"],
        "DAMAGE_REPORTED": ["DAMAGE_RESOLVED"],
        "DAMAGE_RESOLVED": ["EN_ROUTE", "DESTINATION_HUB"],
        "RETURN_TO_SENDER": ["COLLECTED", "WAREHOUSE_PROCESSING", "DELIVERED"],
        "TRANSIT_EXCEPTION": ["EN_ROUTE", "DESTINATION_HUB"],
        "DESTINATION_HUB": ["WITH_COURIER"],
        "WITH_COURIER": ["DELIVERED"],
        "DELIVERED": []
    }
    
    available = status_flow.get(shipment.current_status, [])
    
    # Check if customs is required for international shipments
    requires_customs = shipment.is_international and shipment.current_status in ["EN_ROUTE", "TERMINAL_ARRIVAL"]
    
    return {
        "current": shipment.current_status,
        "current_display": SHIPMENT_STATUSES.get(shipment.current_status, shipment.current_status),
        "available": available,
        "available_display": [SHIPMENT_STATUSES.get(s, s) for s in available],
        "requires_customs": requires_customs
    }

def _calculate_duration(start, end):
    """Calculate duration between two timestamps"""
    if not start:
        return None
    if not end:
        end = datetime.utcnow()
    duration = end - start
    hours = duration.total_seconds() / 3600
    if hours < 24:
        return f"{int(hours)} hours"
    else:
        days = int(hours / 24)
        return f"{days} days"