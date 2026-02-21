# Eukexpress\backend\app\api\v1\dashboard.py
"""
Layer 1: Dashboard Endpoints
Overview statistics and recent activity
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import logging

from app.database import get_db
from app.models import Shipment, StatusHistory
from app.api.v1.auth import oauth2_scheme
from app.services import auth_service
from app.utils.constants import SHIPMENT_STATUSES

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/")
async def get_dashboard(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Get dashboard overview statistics
    Returns counts and recent activity for Layer 1
    """
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    logger.info(f"Dashboard accessed by admin: {payload.get('sub')}")
    
    # Get current date range
    today = datetime.now().date()
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    
    # Calculate statistics
    stats = {
        "active_shipments": db.query(Shipment).filter(
            Shipment.current_status.notin_(['DELIVERED', 'RETURN_TO_SENDER'])
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
        
        "attention_required": db.query(Shipment).filter(
            and_(
                Shipment.current_status.notin_(['DELIVERED', 'RETURN_TO_SENDER']),
                Shipment.updated_at < datetime.now() - timedelta(days=3)
            )
        ).count(),
    }
    
    # Calculate revenue (using declared_value as proxy for revenue)
    revenue_result = db.query(
        func.sum(Shipment.declared_value)
    ).filter(
        Shipment.created_at >= month_start
    ).scalar()
    
    stats["revenue_month"] = float(revenue_result) if revenue_result else 0
    
    # Get recent activity (last 10 status changes)
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
                "event": f"{activity.previous_status} → {activity.new_status}",
                "event_display": SHIPMENT_STATUSES.get(activity.new_status, activity.new_status),
                "timestamp": activity.created_at.isoformat(),
                "location": activity.location
            })
    
    return {
        "stats": stats,
        "recent_activity": activity_list
    }

@router.get("/quick-actions")
async def get_quick_actions(
    token: str = Depends(oauth2_scheme)
):
    """
    Get available quick actions for dashboard
    """
    return {
        "actions": [
            {
                "name": "Create Shipment",
                "url": "/admin/create.html",
                "icon": "plus-circle",
                "description": "Register a new shipment"
            },
            {
                "name": "Shipment History",
                "url": "/admin/history.html",
                "icon": "list",
                "description": "View all shipments"
            },
            {
                "name": "Bulk Email",
                "url": "/admin/bulk-email.html",
                "icon": "envelope",
                "description": "Send mass communications"
            }
        ]
    }