# Eukexpress\backend\app\services\intervention_service.py
"""
Intervention Service
Handles all intervention operations (customs, security, damage, returns, delays)
"""
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import uuid
from typing import Optional, Dict, Any

from app.models.shipment import Shipment
from app.models.status_history import StatusHistory
from app.services import notification_service

logger = logging.getLogger(__name__)

def toggle_customs_bond(db: Session, shipment_id: str, user_id: str) -> Dict[str, Any]:
    """Toggle customs bond status for a shipment"""
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return {"success": False, "error": "Shipment not found"}
        
        # Toggle the status
        shipment.customs_bond_active = not shipment.customs_bond_active
        shipment.updated_at = datetime.utcnow()
        
        # Create status history
        status = "customs_bond_activated" if shipment.customs_bond_active else "customs_bond_deactivated"
        create_intervention_history(
            db, 
            shipment_id, 
            status, 
            user_id,
            f"Customs bond {'activated' if shipment.customs_bond_active else 'deactivated'}"
        )
        
        db.commit()
        
        return {
            "success": True,
            "customs_bond_active": shipment.customs_bond_active
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error toggling customs bond: {e}")
        return {"success": False, "error": str(e)}

def toggle_security_hold(db: Session, shipment_id: str, user_id: str) -> Dict[str, Any]:
    """Toggle security hold status for a shipment"""
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return {"success": False, "error": "Shipment not found"}
        
        # Toggle the status
        shipment.security_hold_active = not shipment.security_hold_active
        shipment.updated_at = datetime.utcnow()
        
        # Create status history
        status = "security_hold_activated" if shipment.security_hold_active else "security_hold_deactivated"
        create_intervention_history(
            db, 
            shipment_id, 
            status, 
            user_id,
            f"Security hold {'activated' if shipment.security_hold_active else 'deactivated'}"
        )
        
        db.commit()
        
        return {
            "success": True,
            "security_hold_active": shipment.security_hold_active
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error toggling security hold: {e}")
        return {"success": False, "error": str(e)}

def report_damage(db: Session, shipment_id: str, user_id: str, description: str) -> Dict[str, Any]:
    """Report damage for a shipment"""
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return {"success": False, "error": "Shipment not found"}
        
        # Set damage reported
        shipment.damage_reported = True
        shipment.damage_description = description
        shipment.damage_reported_date = datetime.utcnow()
        shipment.damage_reported_by = user_id
        shipment.updated_at = datetime.utcnow()
        
        # Create status history
        create_intervention_history(
            db, 
            shipment_id, 
            "damage_reported", 
            user_id,
            f"Damage reported: {description}"
        )
        
        db.commit()
        
        return {
            "success": True,
            "damage_reported": True,
            "damage_description": description
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error reporting damage: {e}")
        return {"success": False, "error": str(e)}

def resolve_damage(db: Session, shipment_id: str, user_id: str, resolution: str) -> Dict[str, Any]:
    """Resolve reported damage for a shipment"""
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return {"success": False, "error": "Shipment not found"}
        
        if not shipment.damage_reported:
            return {"success": False, "error": "No damage reported for this shipment"}
        
        # Resolve damage
        shipment.damage_reported = False
        shipment.damage_resolved = True
        shipment.damage_resolution = resolution
        shipment.damage_resolved_date = datetime.utcnow()
        shipment.damage_resolved_by = user_id
        shipment.updated_at = datetime.utcnow()
        
        # Create status history
        create_intervention_history(
            db, 
            shipment_id, 
            "damage_resolved", 
            user_id,
            f"Damage resolved: {resolution}"
        )
        
        db.commit()
        
        return {
            "success": True,
            "damage_reported": False,
            "damage_resolved": True
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error resolving damage: {e}")
        return {"success": False, "error": str(e)}

def initiate_return(db: Session, shipment_id: str, user_id: str, reason: str) -> Dict[str, Any]:
    """Initiate return for a shipment"""
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return {"success": False, "error": "Shipment not found"}
        
        # Set return initiated
        shipment.return_initiated = True
        shipment.return_reason = reason
        shipment.return_initiated_date = datetime.utcnow()
        shipment.return_initiated_by = user_id
        shipment.updated_at = datetime.utcnow()
        
        # Update status
        old_status = shipment.current_status
        shipment.current_status = "return_initiated"
        
        # Create status history
        create_intervention_history(
            db, 
            shipment_id, 
            "return_initiated", 
            user_id,
            f"Return initiated: {reason}"
        )
        
        db.commit()
        
        return {
            "success": True,
            "return_initiated": True,
            "current_status": "return_initiated"
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error initiating return: {e}")
        return {"success": False, "error": str(e)}

def cancel_return(db: Session, shipment_id: str, user_id: str) -> Dict[str, Any]:
    """Cancel initiated return for a shipment"""
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return {"success": False, "error": "Shipment not found"}
        
        if not shipment.return_initiated:
            return {"success": False, "error": "No return initiated for this shipment"}
        
        # Cancel return
        shipment.return_initiated = False
        shipment.return_cancelled = True
        shipment.return_cancelled_date = datetime.utcnow()
        shipment.return_cancelled_by = user_id
        shipment.updated_at = datetime.utcnow()
        
        # Restore previous status (default to 'pending' if can't determine)
        shipment.current_status = "pending"
        
        # Create status history
        create_intervention_history(
            db, 
            shipment_id, 
            "return_cancelled", 
            user_id,
            "Return cancelled"
        )
        
        db.commit()
        
        return {
            "success": True,
            "return_initiated": False,
            "return_cancelled": True
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error cancelling return: {e}")
        return {"success": False, "error": str(e)}

def report_delay(db: Session, shipment_id: str, user_id: str, reason: str, estimated_days: int) -> Dict[str, Any]:
    """Report delay for a shipment"""
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return {"success": False, "error": "Shipment not found"}
        
        # Set delay
        shipment.delay_active = True
        shipment.delay_reason = reason
        shipment.delay_estimated_days = estimated_days
        shipment.delay_reported_date = datetime.utcnow()
        shipment.delay_reported_by = user_id
        shipment.updated_at = datetime.utcnow()
        
        # Update status if needed
        if shipment.current_status not in ["delayed", "return_initiated"]:
            old_status = shipment.current_status
            shipment.current_status = "delayed"
        
        # Create status history
        create_intervention_history(
            db, 
            shipment_id, 
            "delay_reported", 
            user_id,
            f"Delay reported: {reason}, estimated {estimated_days} days"
        )
        
        db.commit()
        
        return {
            "success": True,
            "delay_active": True,
            "delay_reason": reason,
            "estimated_days": estimated_days
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error reporting delay: {e}")
        return {"success": False, "error": str(e)}

def resolve_delay(db: Session, shipment_id: str, user_id: str) -> Dict[str, Any]:
    """Resolve reported delay for a shipment"""
    try:
        shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
        if not shipment:
            return {"success": False, "error": "Shipment not found"}
        
        if not shipment.delay_active:
            return {"success": False, "error": "No active delay for this shipment"}
        
        # Resolve delay
        shipment.delay_active = False
        shipment.delay_resolved = True
        shipment.delay_resolved_date = datetime.utcnow()
        shipment.delay_resolved_by = user_id
        shipment.updated_at = datetime.utcnow()
        
        # Restore previous status (default to 'in_transit')
        if shipment.current_status == "delayed":
            shipment.current_status = "in_transit"
        
        # Create status history
        create_intervention_history(
            db, 
            shipment_id, 
            "delay_resolved", 
            user_id,
            "Delay resolved"
        )
        
        db.commit()
        
        return {
            "success": True,
            "delay_active": False,
            "delay_resolved": True
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error resolving delay: {e}")
        return {"success": False, "error": str(e)}

def create_intervention_history(
    db: Session,
    shipment_id: str,
    intervention_type: str,
    user_id: str,
    description: str
) -> StatusHistory:
    """Create a history entry for an intervention"""
    history = StatusHistory(
        id=uuid.uuid4(),
        shipment_id=shipment_id,
        previous_status=None,
        new_status=intervention_type,
        changed_by=user_id,
        location=None,
        notes=description,
        created_at=datetime.utcnow()
    )
    
    db.add(history)
    db.commit()
    db.refresh(history)
    return history

def get_active_interventions(db: Session, shipment_id: str) -> Dict[str, bool]:
    """Get all active interventions for a shipment"""
    shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
    if not shipment:
        return {}
    
    return {
        "customs_bond_active": shipment.customs_bond_active,
        "security_hold_active": shipment.security_hold_active,
        "damage_reported": shipment.damage_reported,
        "return_initiated": shipment.return_initiated,
        "delay_active": shipment.delay_active
    }
