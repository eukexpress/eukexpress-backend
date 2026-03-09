"""
Shipments API Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, File, UploadFile, Form, Request
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional
import logging
from datetime import date, datetime
import random
import string
import hashlib

from app.database import get_db
from app.models.shipment import Shipment
from app.schemas.shipment import StatusUpdate
from app.api.deps import get_current_user_required
from app.utils.constants import SHIPMENT_STATUSES, STATUS_COLORS

router = APIRouter(tags=["Shipments"])
logger = logging.getLogger(__name__)

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_shipment(
    request: Request,
    front_image: UploadFile = File(...),
    rear_image: UploadFile = File(...),
    sender_name: str = Form(...),
    sender_email: str = Form(...),
    sender_phone: str = Form(...),
    sender_address: str = Form(...),
    recipient_name: str = Form(...),
    recipient_email: str = Form(...),
    recipient_phone: str = Form(...),
    recipient_address: str = Form(...),
    origin_location: str = Form(...),
    origin_code: Optional[str] = Form(None),
    destination_location: str = Form(...),
    destination_code: Optional[str] = Form(None),
    goods_description: str = Form(...),
    weight_kg: Optional[float] = Form(None),
    dimensions: Optional[str] = Form(None),
    declared_value: Optional[float] = Form(None),
    declared_currency: str = Form("USD"),
    shipping_amount: float = Form(...),
    payment_method: Optional[str] = Form(None),
    payment_status: str = Form("PENDING"),
    sending_date: str = Form(...),
    estimated_delivery_date: str = Form(...),
    is_international: bool = Form(False),
    current_user = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Create a new shipment"""
    logger.info(f"📦 Create shipment by: {current_user.username}")
    
    # Parse dimensions
    dimensions_dict = None
    if dimensions:
        try:
            dim_parts = dimensions.split('x')
            if len(dim_parts) == 3:
                dimensions_dict = {
                    "length": float(dim_parts[0]),
                    "width": float(dim_parts[1]),
                    "height": float(dim_parts[2])
                }
        except:
            pass
    
    # Generate tracking number
    tracking_number = "EUK" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    invoice_number = "INV-" + datetime.now().strftime("%Y%m%d") + "-" + ''.join(random.choices(string.digits, k=4))
    
    # Read image content for hash
    front_image_content = await front_image.read()
    rear_image_content = await rear_image.read()
    
    front_image_hash = hashlib.sha256(front_image_content).hexdigest()
    rear_image_hash = hashlib.sha256(rear_image_content).hexdigest()
    
    # Reset file position
    await front_image.seek(0)
    await rear_image.seek(0)
    
    # Save files
    front_image_path = f"uploads/shipments/{tracking_number}_front.jpg"
    rear_image_path = f"uploads/shipments/{tracking_number}_rear.jpg"
    
    new_shipment = Shipment(
        tracking_number=tracking_number,
        invoice_number=invoice_number,
        sender_name=sender_name,
        sender_email=sender_email,
        sender_phone=sender_phone,
        sender_address=sender_address,
        recipient_name=recipient_name,
        recipient_email=recipient_email,
        recipient_phone=recipient_phone,
        recipient_address=recipient_address,
        origin_location=origin_location,
        origin_code=origin_code,
        destination_location=destination_location,
        destination_code=destination_code,
        goods_description=goods_description,
        weight_kg=weight_kg,
        dimensions=dimensions_dict,
        declared_value=declared_value,
        declared_currency=declared_currency,
        shipping_amount=shipping_amount,
        payment_method=payment_method,
        payment_status=payment_status,
        sending_date=datetime.strptime(sending_date, "%Y-%m-%d").date(),
        estimated_delivery_date=datetime.strptime(estimated_delivery_date, "%Y-%m-%d").date(),
        is_international=is_international,
        current_status="BOOKED",
        front_image_path=front_image_path,
        rear_image_path=rear_image_path,
        front_image_hash=front_image_hash,
        rear_image_hash=rear_image_hash
    )
    
    db.add(new_shipment)
    db.commit()
    db.refresh(new_shipment)
    
    logger.info(f"📦 Shipment created: {tracking_number}")
    
    return {
        "success": True,
        "message": "Shipment created successfully",
        "data": {
            "tracking_number": tracking_number,
            "invoice_number": invoice_number,
            "id": str(new_shipment.id)
        }
    }

@router.get("/")
async def get_shipments(
    request: Request,
    current_user = Depends(get_current_user_required),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None)
):
    """Get paginated list of shipments"""
    logger.info("="*50)
    logger.info("📦 SHIPMENTS LIST ENDPOINT HIT")
    logger.info(f"User: {current_user.username if current_user else 'None'}")
    logger.info(f"User ID: {current_user.id if current_user else 'None'}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info("="*50)

    query = db.query(Shipment)

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

    total = query.count()
    offset = (page - 1) * limit
    pages = (total + limit - 1) // limit

    shipments = query.order_by(Shipment.created_at.desc())\
                     .offset(offset)\
                     .limit(limit)\
                     .all()

    shipment_list = []
    for shipment in shipments:
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
    current_user = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get available filter options"""
    logger.info(f"🔍 Filters accessed by: {current_user.username}")

    db_statuses = db.query(Shipment.current_status).distinct().all()
    statuses = [s[0] for s in db_statuses if s[0]]

    status_options = [
        {"value": s, "label": SHIPMENT_STATUSES.get(s, s)}
        for s in statuses
    ]

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
    current_user = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get shipment details by tracking number"""
    logger.info(f"📋 Shipment details for: {tracking_number} by: {current_user.username}")
    
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
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
            "origin_code": shipment.origin_code,
            "destination_location": shipment.destination_location,
            "destination_code": shipment.destination_code,
            "goods_description": shipment.goods_description,
            "weight_kg": float(shipment.weight_kg) if shipment.weight_kg else None,
            "dimensions": shipment.dimensions,
            "declared_value": float(shipment.declared_value) if shipment.declared_value else None,
            "declared_currency": shipment.declared_currency,
            "shipping_amount": float(shipment.shipping_amount) if shipment.shipping_amount else None,
            "payment_method": shipment.payment_method,
            "payment_status": shipment.payment_status,
            "current_status": shipment.current_status,
            "customs_bond_active": shipment.customs_bond_active,
            "security_hold_active": shipment.security_hold_active,
            "damage_reported": shipment.damage_reported,
            "return_active": getattr(shipment, 'return_active', False),
            "delay_active": shipment.delay_active,
            "sending_date": shipment.sending_date.isoformat() if shipment.sending_date else None,
            "estimated_delivery_date": shipment.estimated_delivery_date.isoformat() if shipment.estimated_delivery_date else None,
            "actual_delivery_date": shipment.actual_delivery_date.isoformat() if shipment.actual_delivery_date else None,
            "is_international": shipment.is_international,
            "front_image_path": shipment.front_image_path,
            "rear_image_path": shipment.rear_image_path,
            "created_at": shipment.created_at.isoformat() if shipment.created_at else None,
            "updated_at": shipment.updated_at.isoformat() if shipment.updated_at else None
        }
    }

@router.post("/{tracking_number}/status")
async def update_status(
    tracking_number: str,
    status_update: StatusUpdate,
    current_user = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Update shipment status"""
    logger.info(f"🔄 Status update for: {tracking_number} by: {current_user.username}")
    
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    old_status = shipment.current_status
    shipment.current_status = status_update.status
    shipment.updated_at = datetime.utcnow()
    
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

@router.get("/{tracking_number}/available-statuses")
async def get_available_statuses(
    tracking_number: str,
    current_user = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get available status transitions"""
    logger.info(f"📋 Available statuses for: {tracking_number} by: {current_user.username}")
    
    shipment = db.query(Shipment).filter(
        Shipment.tracking_number == tracking_number.upper()
    ).first()
    
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shipment not found"
        )
    
    status_flow = {
        "BOOKED": ["PROCESSING", "CANCELLED"],
        "PROCESSING": ["IN_TRANSIT", "CANCELLED"],
        "IN_TRANSIT": ["OUT_FOR_DELIVERY", "DELAYED"],
        "OUT_FOR_DELIVERY": ["DELIVERED", "DELAYED"],
        "DELAYED": ["IN_TRANSIT"],
        "DELIVERED": ["COMPLETED"],
        "COMPLETED": [],
        "CANCELLED": []
    }
    
    available = status_flow.get(shipment.current_status, [])
    
    return {
        "success": True,
        "data": {
            "current_status": shipment.current_status,
            "current_status_display": SHIPMENT_STATUSES.get(shipment.current_status, shipment.current_status),
            "available_statuses": [
                {
                    "status": s,
                    "display": SHIPMENT_STATUSES.get(s, s)
                }
                for s in available
            ]
        }
    }

# Export router with expected name - THIS IS CRITICAL
shipments_router = router