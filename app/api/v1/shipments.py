"""
Shipments API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
import logging
from datetime import date, datetime  # FIXED: Added datetime import

from app.database import get_db
from app.models.shipment import Shipment
from app.schemas.shipment import StatusUpdate
from app.api.v1.auth import oauth2_scheme
from app.services import auth_service
from app.utils.constants import SHIPMENT_STATUSES, STATUS_COLORS

router = APIRouter(tags=["Shipments"])
logger = logging.getLogger(__name__)

@router.get("/")
async def get_shipments(
    request: Request,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get paginated list of shipments with filters"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    logger.info(f"Shipment list accessed by admin: {payload.get('sub')}")

    # Build base query
    query = db.query(Shipment)

    # Apply filters
    if status:
        query = query.filter(Shipment.current_status == status)

    if search:
        search_filter = or_(
            Shipment.tracking_number.ilike(f"%{search}%"),
            Shipment.invoice_number.ilike(f"%{search}%"),
            Shipment.sender_name.ilike(f"%{search}%"),
            Shipment.recipient_name.ilike(f"%{search}%"),
            Shipment.origin_location.ilike(f"%{search}%"),
            Shipment.destination_location.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    if date_from:
        query = query.filter(func.date(Shipment.created_at) >= date_from)

    if date_to:
        query = query.filter(func.date(Shipment.created_at) <= date_to)

    # Get total count
    total = query.count()

    # Calculate pagination
    offset = (page - 1) * limit
    pages = (total + limit - 1) // limit

    # Get shipments with pagination
    shipments = query.order_by(Shipment.created_at.desc())\
                     .offset(offset)\
                     .limit(limit)\
                     .all()

    # Transform to response format
    shipment_list = []
    for shipment in shipments:
        # Determine if shipment has active interventions
        has_interventions = any([
            shipment.customs_bond_active,
            shipment.security_hold_active,
            shipment.damage_reported,
            getattr(shipment, 'return_active', False),
            shipment.delay_active
        ])

        intervention_types = []
        if shipment.customs_bond_active:
            intervention_types.append("customs")
        if shipment.security_hold_active:
            intervention_types.append("security")
        if shipment.damage_reported:
            intervention_types.append("damage")
        if getattr(shipment, 'return_active', False):
            intervention_types.append("return")
        if shipment.delay_active:
            intervention_types.append("delay")

        shipment_list.append({
            "tracking_number": shipment.tracking_number,
            "status": shipment.current_status,
            "status_display": SHIPMENT_STATUSES.get(shipment.current_status, shipment.current_status),
            "status_color": STATUS_COLORS.get(shipment.current_status, "gray"),
            "origin_location": shipment.origin_location,
            "destination_location": shipment.destination_location,
            "sender_name": shipment.sender_name,
            "recipient_name": shipment.recipient_name,
            "last_update": shipment.updated_at.isoformat() if shipment.updated_at else None,
            "has_interventions": has_interventions,
            "intervention_types": intervention_types
        })

    return {
        "success": True,
        "data": {
            "total": total,
            "page": page,
            "pages": pages,
            "limit": limit,
            "shipments": shipment_list
        }
    }

@router.get("/filters")
async def get_filters(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get available filter options for shipments"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get distinct statuses
    db_statuses = db.query(Shipment.current_status).distinct().all()
    statuses = [s[0] for s in db_statuses if s[0]]

    # Get status display names
    status_options = [
        {"value": s, "label": SHIPMENT_STATUSES.get(s, s)}
        for s in statuses
    ]

    # Get distinct locations
    origins = db.query(Shipment.origin_location).distinct().limit(10).all()
    destinations = db.query(Shipment.destination_location).distinct().limit(10).all()

    locations = list(set([o[0] for o in origins if o[0]] + [d[0] for d in destinations if d[0]]))

    return {
        "success": True,
        "data": {
            "statuses": status_options,
            "locations": locations
        }
    }

@router.get("/{tracking_number}")
async def get_shipment(
    tracking_number: str,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Get shipment details by tracking number"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    return {
        "success": True,
        "data": {
            "id": str(shipment.id),
            "tracking_number": shipment.tracking_number,
            "invoice_number": shipment.invoice_number,
            "sender_name": shipment.sender_name,
            "sender_email": shipment.sender_email,
            "sender_phone": shipment.sender_phone,
            "sender_address": shipment.sender_address,
            "recipient_name": shipment.recipient_name,
            "recipient_email": shipment.recipient_email,
            "recipient_phone": shipment.recipient_phone,
            "recipient_address": shipment.recipient_address,
            "origin_location": shipment.origin_location,
            "destination_location": shipment.destination_location,
            "goods_description": shipment.goods_description,
            "weight_kg": float(shipment.weight_kg) if shipment.weight_kg else None,
            "dimensions": shipment.dimensions,
            "declared_value": float(shipment.declared_value) if shipment.declared_value else None,
            "current_status": shipment.current_status,
            "customs_bond_active": shipment.customs_bond_active,
            "security_hold_active": shipment.security_hold_active,
            "damage_reported": shipment.damage_reported,
            "delay_active": shipment.delay_active,
            "sending_date": shipment.sending_date.isoformat() if shipment.sending_date else None,
            "estimated_delivery_date": shipment.estimated_delivery_date.isoformat() if shipment.estimated_delivery_date else None,
            "actual_delivery_date": shipment.actual_delivery_date.isoformat() if shipment.actual_delivery_date else None,
            "created_at": shipment.created_at.isoformat() if shipment.created_at else None,
            "updated_at": shipment.updated_at.isoformat() if shipment.updated_at else None
        }
    }

@router.post("/{tracking_number}/status")
async def update_status(
    tracking_number: str,
    status_update: StatusUpdate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Update shipment status"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    
    # Update status
    old_status = shipment.current_status
    shipment.current_status = status_update.status
    shipment.updated_at = datetime.utcnow()  # FIXED: Now datetime is defined
    
    db.commit()
    
    return {
        "success": True,
        "message": "Status updated successfully",
        "data": {
            "tracking_number": tracking_number,
            "old_status": old_status,
            "new_status": status_update.status
        }
    }