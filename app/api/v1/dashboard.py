#app/api/v1/dashboard.py
"""
Dashboard Endpoints
"""

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models import Shipment, StatusHistory
from app.api.deps import get_current_user_required
from app.utils.constants import SHIPMENT_STATUSES

router = APIRouter(tags=["Dashboard"])
logger = logging.getLogger(__name__)

@router.get("/")
async def get_dashboard(
    request: Request,
    current_user = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    logger.info("="*50)
    logger.info("📊 DASHBOARD MAIN ENDPOINT HIT")
    logger.info(f"User: {current_user.username if current_user else 'None'}")
    logger.info(f"User ID: {current_user.id if current_user else 'None'}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info("="*50)
    
    today = datetime.now().date()
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    
    stats = {
        "active_shipments": db.query(Shipment).filter(
            Shipment.current_status.notin_(['DELIVERED', 'CANCELLED'])
        ).count(),
        "today_shipments": db.query(Shipment).filter(
            func.date(Shipment.created_at) == today
        ).count(),
        "delayed_count": db.query(Shipment).filter(
            Shipment.delay_active == True
        ).count(),
        "customs_bond_count": db.query(Shipment).filter(
            Shipment.customs_bond_active == True
        ).count(),
        "damage_reported_count": db.query(Shipment).filter(
            Shipment.damage_reported == True
        ).count(),
        "security_hold_count": db.query(Shipment).filter(
            Shipment.security_hold_active == True
        ).count(),
        "total_shipments": db.query(Shipment).count(),
    }
    
    revenue_result = db.query(
        func.sum(Shipment.shipping_amount)
    ).filter(
        Shipment.created_at >= month_start
    ).scalar()
    
    stats["revenue_month"] = float(revenue_result) if revenue_result else 0
    
    recent_activity = db.query(StatusHistory)\
        .order_by(StatusHistory.created_at.desc())\
        .limit(10)\
        .all()
    
    activity_list = []
    for activity in recent_activity:
        shipment = db.query(Shipment).filter(
            Shipment.id == activity.shipment_id
        ).first()
        
        if shipment:
            activity_list.append({
                "tracking": shipment.tracking_number,
                "event": activity.new_status,
                "event_display": SHIPMENT_STATUSES.get(activity.new_status, activity.new_status),
                "timestamp": activity.created_at.isoformat() if activity.created_at else None,
                "location": activity.location
            })
    
    return {
        "success": True,
        "data": {
            "stats": stats,
            "recent_activity": activity_list,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

@router.get("/quick-actions")
async def get_quick_actions(
    current_user = Depends(get_current_user_required),
    db: Session = Depends(get_db)
):
    """Get available quick actions"""
    pending_count = db.query(Shipment).filter(
        Shipment.current_status == 'PENDING'
    ).count()
    
    intervention_count = db.query(Shipment).filter(
        (Shipment.customs_bond_active == True) |
        (Shipment.security_hold_active == True) |
        (Shipment.damage_reported == True) |
        (Shipment.delay_active == True)
    ).count()
    
    return {
        "success": True,
        "data": {
            "actions": [
                {"name": "Create Shipment", "url": "/admin/create.html", "icon": "plus-circle", "description": "Register a new shipment", "count": None},
                {"name": "Process Pending", "url": "/admin/shipments?status=PENDING", "icon": "clock", "description": f"{pending_count} shipments waiting", "count": pending_count},
                {"name": "Handle Interventions", "url": "/admin/interventions", "icon": "exclamation-triangle", "description": f"{intervention_count} shipments need attention", "count": intervention_count}
            ]
        }
    }

@router.get("/recent-shipments")
async def get_recent_shipments(
    current_user = Depends(get_current_user_required),
    db: Session = Depends(get_db),
    limit: int = 5
):
    """Get most recent shipments"""
    recent = db.query(Shipment)\
        .order_by(Shipment.created_at.desc())\
        .limit(limit)\
        .all()
    
    shipments = []
    for shipment in recent:
        shipments.append({
            "tracking": shipment.tracking_number,
            "status": shipment.current_status,
            "status_display": SHIPMENT_STATUSES.get(shipment.current_status, shipment.current_status),
            "origin": shipment.origin_location,
            "destination": shipment.destination_location,
            "recipient": shipment.recipient_name
        })
    
    return {"success": True, "data": shipments}

# Export router with expected name - THIS WAS MISSING!
dashboard_router = router