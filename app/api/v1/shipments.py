#Eukexpress\backend\app\api\v1\shipments.py
"""
Layer 2: Shipment History Endpoints
Paginated list of all shipments with filtering
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import Optional, List
from datetime import date, datetime
import logging

from app.database import get_db
from app.models import Shipment
from app.schemas.shipment import ShipmentListItem
from app.api.v1.auth import oauth2_scheme
from app.services import auth_service, tracking_service
from app.utils.constants import SHIPMENT_STATUSES, STATUS_COLORS

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=dict)
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
    """
    Get paginated list of all shipments with filtering
    Layer 2: Shipment History
    """
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
            shipment.return_active,
            shipment.delay_active
        ])
        
        intervention_types = []
        if shipment.customs_bond_active:
            intervention_types.append("customs")
        if shipment.security_hold_active:
            intervention_types.append("security")
        if shipment.damage_reported:
            intervention_types.append("damage")
        if shipment.return_active:
            intervention_types.append("return")
        if shipment.delay_active:
            intervention_types.append("delay")
        
        shipment_list.append({
            "tracking": shipment.tracking_number,
            "status": shipment.current_status,
            "status_display": SHIPMENT_STATUSES.get(shipment.current_status, shipment.current_status),
            "status_color": STATUS_COLORS.get(shipment.current_status, "gray"),
            "origin": shipment.origin_location,
            "destination": shipment.destination_location,
            "sender_name": shipment.sender_name,
            "recipient_name": shipment.recipient_name,
            "last_update": shipment.updated_at.isoformat(),
            "last_update_display": shipment.updated_at.strftime("%Y-%m-%d %H:%M"),
            "has_interventions": has_interventions,
            "intervention_types": intervention_types
        })
    
    return {
        "total": total,
        "page": page,
        "pages": pages,
        "limit": limit,
        "shipments": shipment_list
    }

@router.get("/filters")
async def get_filter_options(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Get available filter options for shipment list
    """
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get distinct statuses that actually exist in database
    db_statuses = db.query(Shipment.current_status).distinct().all()
    statuses = [s[0] for s in db_statuses]
    
    # Get status display names
    status_options = [
        {"value": s, "label": SHIPMENT_STATUSES.get(s, s)}
        for s in statuses
    ]
    
    # Get date range options
    date_ranges = [
        {"value": "today", "label": "Today"},
        {"value": "yesterday", "label": "Yesterday"},
        {"value": "this_week", "label": "This Week"},
        {"value": "this_month", "label": "This Month"},
        {"value": "last_month", "label": "Last Month"},
        {"value": "custom", "label": "Custom Range"}
    ]
    
    # Get distinct locations
    origins = db.query(Shipment.origin_location).distinct().limit(10).all()
    destinations = db.query(Shipment.destination_location).distinct().limit(10).all()
    
    locations = list(set([o[0] for o in origins] + [d[0] for d in destinations]))
    
    return {
        "statuses": status_options,
        "date_ranges": date_ranges,
        "locations": locations
    }

@router.get("/export")
async def export_shipments(
    format: str = Query("csv", regex="^(csv|excel)$"),
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Export shipments data to CSV or Excel
    """
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Build query (similar to get_shipments but without pagination)
    query = db.query(Shipment)
    
    if status:
        query = query.filter(Shipment.current_status == status)
    
    if date_from:
        query = query.filter(func.date(Shipment.created_at) >= date_from)
    
    if date_to:
        query = query.filter(func.date(Shipment.created_at) <= date_to)
    
    shipments = query.order_by(Shipment.created_at.desc()).all()
    
    # TODO: Generate CSV/Excel file
    # This would be implemented with a library like pandas or csv module
    
    return {
        "message": f"Export functionality would return {len(shipments)} shipments in {format} format",
        "count": len(shipments)
    }