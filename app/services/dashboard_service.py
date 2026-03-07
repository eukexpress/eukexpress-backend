"""
Dashboard Service
Provides statistics and metrics for the admin dashboard
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, List

from app.models.shipment import Shipment
from app.models.admin import Admin
from app.models.status_history import StatusHistory

logger = logging.getLogger(__name__)

def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    """Get comprehensive dashboard statistics"""
    try:
        # Current date and date ranges
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Basic counts
        total_shipments = db.query(Shipment).count()
        
        # Shipments by status
        status_counts = {}
        statuses = db.query(Shipment.current_status, func.count(Shipment.id)).group_by(Shipment.current_status).all()
        for status, count in statuses:
            status_counts[status] = count
        
        # Today's shipments
        today_shipments = db.query(Shipment).filter(Shipment.created_at >= today_start).count()
        
        # This week's shipments
        week_shipments = db.query(Shipment).filter(Shipment.created_at >= week_ago).count()
        
        # This month's shipments
        month_shipments = db.query(Shipment).filter(Shipment.created_at >= month_ago).count()
        
        # Active interventions
        active_interventions = {
            "customs_bond": db.query(Shipment).filter(Shipment.customs_bond_active == True).count(),
            "security_hold": db.query(Shipment).filter(Shipment.security_hold_active == True).count(),
            "damage_reported": db.query(Shipment).filter(Shipment.damage_reported == True).count(),
            "return_initiated": db.query(Shipment).filter(Shipment.return_initiated == True).count(),
            "delay_active": db.query(Shipment).filter(Shipment.delay_active == True).count()
        }
        
        # Recent activity (last 10 status changes)
        recent_activity = db.query(StatusHistory)\
            .order_by(StatusHistory.created_at.desc())\
            .limit(10)\
            .all()
        
        recent_activity_formatted = []
        for activity in recent_activity:
            shipment = db.query(Shipment).filter(Shipment.id == activity.shipment_id).first()
            recent_activity_formatted.append({
                "id": str(activity.id),
                "shipment_id": str(activity.shipment_id),
                "tracking_number": shipment.tracking_number if shipment else "Unknown",
                "event": activity.new_status,
                "location": activity.location,
                "timestamp": activity.created_at.isoformat() if activity.created_at else None,
                "changed_by": activity.changed_by
            })
        
        # Shipments by origin/destination (top 5)
        top_origins = db.query(Shipment.origin_location, func.count(Shipment.id).label('count'))\
            .group_by(Shipment.origin_location)\
            .order_by(func.count(Shipment.id).desc())\
            .limit(5)\
            .all()
        
        top_destinations = db.query(Shipment.destination_location, func.count(Shipment.id).label('count'))\
            .group_by(Shipment.destination_location)\
            .order_by(func.count(Shipment.id).desc())\
            .limit(5)\
            .all()
        
        # Delivery performance
        on_time_deliveries = db.query(Shipment)\
            .filter(
                Shipment.actual_delivery_date.isnot(None),
                Shipment.estimated_delivery_date.isnot(None),
                Shipment.actual_delivery_date <= Shipment.estimated_delivery_date
            )\
            .count()
        
        total_delivered = db.query(Shipment)\
            .filter(Shipment.actual_delivery_date.isnot(None))\
            .count()
        
        on_time_percentage = (on_time_deliveries / total_delivered * 100) if total_delivered > 0 else 0
        
        return {
            "success": True,
            "stats": {
                "overview": {
                    "total_shipments": total_shipments,
                    "today_shipments": today_shipments,
                    "week_shipments": week_shipments,
                    "month_shipments": month_shipments
                },
                "status_breakdown": status_counts,
                "active_interventions": active_interventions,
                "recent_activity": recent_activity_formatted,
                "top_routes": {
                    "origins": [{"location": o[0], "count": o[1]} for o in top_origins],
                    "destinations": [{"location": d[0], "count": d[1]} for d in top_destinations]
                },
                "performance": {
                    "total_delivered": total_delivered,
                    "on_time_deliveries": on_time_deliveries,
                    "on_time_percentage": round(on_time_percentage, 2)
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {"success": False, "error": str(e)}

def get_quick_actions(db: Session) -> List[Dict[str, Any]]:
    """Get quick actions for the dashboard"""
    try:
        # Shipments needing attention
        pending_shipments = db.query(Shipment)\
            .filter(Shipment.current_status == "pending")\
            .count()
        
        shipments_with_interventions = db.query(Shipment)\
            .filter(
                (Shipment.customs_bond_active == True) |
                (Shipment.security_hold_active == True) |
                (Shipment.damage_reported == True) |
                (Shipment.return_initiated == True) |
                (Shipment.delay_active == True)
            )\
            .count()
        
        return [
            {
                "id": "process_pending",
                "title": "Process Pending Shipments",
                "description": f"{pending_shipments} shipments waiting",
                "icon": "pending",
                "link": "/shipments?status=pending",
                "priority": "high" if pending_shipments > 10 else "medium"
            },
            {
                "id": "handle_interventions",
                "title": "Handle Interventions",
                "description": f"{shipments_with_interventions} shipments need attention",
                "icon": "warning",
                "link": "/interventions",
                "priority": "high" if shipments_with_interventions > 5 else "medium"
            },
            {
                "id": "generate_report",
                "title": "Generate Weekly Report",
                "description": "Export shipment data for this week",
                "icon": "report",
                "link": "/reports/weekly",
                "priority": "low"
            }
        ]
    except Exception as e:
        logger.error(f"Error getting quick actions: {e}")
        return []

def get_recent_shipments(db: Session, limit: int = 5) -> List[Dict[str, Any]]:
    """Get recent shipments for dashboard"""
    try:
        shipments = db.query(Shipment)\
            .order_by(Shipment.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [
            {
                "id": str(s.id),
                "tracking_number": s.tracking_number,
                "status": s.current_status,
                "origin": s.origin_location,
                "destination": s.destination_location,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "recipient": s.recipient_name
            }
            for s in shipments
        ]
    except Exception as e:
        logger.error(f"Error getting recent shipments: {e}")
        return []
