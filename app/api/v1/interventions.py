"""
Intervention Toggle Endpoints
All intervention controls for shipments
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.database import get_db
from app.models import Shipment, InterventionLog
from app.schemas.intervention import (
    CustomsIntervention, SecurityIntervention, DamageIntervention,
    ReturnIntervention, DelayIntervention, InterventionResponse
)
from app.api.v1.auth import oauth2_scheme
from app.services import auth_service, email_service
from app.utils.constants import INTERVENTION_TYPES

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{tracking}/interventions/customs", response_model=InterventionResponse)
async def toggle_customs(
    tracking: str,
    intervention: CustomsIntervention,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Activate or release customs bond"""
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
    
    # Record previous state
    previous_state = shipment.customs_bond_active
    now = datetime.utcnow()
    
    email_sent = False
    
    # Update based on action
    if intervention.action == "activate":
        shipment.customs_bond_active = True
        shipment.customs_bond_activated_at = now
        shipment.customs_bond_location = intervention.location
        shipment.customs_bond_reference = intervention.reference
        shipment.customs_bond_notes = intervention.notes
        shipment.current_status = "CUSTOMS_BOND"
        
        # Log intervention
        log = InterventionLog(
            shipment_id=shipment.id,
            intervention_type="customs",
            action="activate",
            previous_state=previous_state,
            new_state=True,
            notes=intervention.notes
        )
        db.add(log)
        
        # Send email notification
        try:
            logger.info(f"📧 Sending customs activation email for {tracking}")
            email_sent = await email_service.send_customs_notification(
                shipment, "activate", 
                {
                    "location": intervention.location,
                    "reference": intervention.reference,
                    "notes": intervention.notes
                }
            )
            logger.info(f"✅ Customs activation email sent: {email_sent}")
        except Exception as e:
            logger.error(f"❌ Failed to send customs activation email: {e}", exc_info=True)
        
    elif intervention.action == "release":
        shipment.customs_bond_active = False
        shipment.customs_bond_released_at = now
        shipment.current_status = "CUSTOMS_CLEARED"
        
        # Log intervention
        log = InterventionLog(
            shipment_id=shipment.id,
            intervention_type="customs",
            action="release",
            previous_state=previous_state,
            new_state=False,
            notes=intervention.notes
        )
        db.add(log)
        
        # Send email notification
        try:
            logger.info(f"📧 Sending customs release email for {tracking}")
            email_sent = await email_service.send_customs_notification(
                shipment, "release",
                {
                    "location": intervention.location,
                    "notes": intervention.notes
                }
            )
            logger.info(f"✅ Customs release email sent: {email_sent}")
        except Exception as e:
            logger.error(f"❌ Failed to send customs release email: {e}", exc_info=True)
    
    # Update shipment
    shipment.status_updated_at = now
    db.commit()
    
    logger.info(f"Customs {intervention.action} for {tracking}")
    
    return InterventionResponse(
        success=True,
        intervention_type="customs",
        action=intervention.action,
        new_state=shipment.customs_bond_active,
        timestamp=now,
        email_sent=email_sent,
        message=f"Customs bond {intervention.action}d successfully"
    )

@router.post("/{tracking}/interventions/security", response_model=InterventionResponse)
async def toggle_security(
    tracking: str,
    intervention: SecurityIntervention,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Activate or clear security hold"""
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
    
    # Record previous state
    previous_state = shipment.security_hold_active
    now = datetime.utcnow()
    
    email_sent = False
    
    # Update based on action
    if intervention.action == "activate":
        shipment.security_hold_active = True
        shipment.security_hold_activated_at = now
        shipment.security_hold_location = intervention.location
        shipment.security_hold_notes = intervention.notes
        shipment.current_status = "SECURITY_HOLD"
        
        # Log intervention
        log = InterventionLog(
            shipment_id=shipment.id,
            intervention_type="security",
            action="activate",
            previous_state=previous_state,
            new_state=True,
            notes=intervention.notes
        )
        db.add(log)
        
        # Send email notification
        try:
            logger.info(f"📧 Sending security activation email for {tracking}")
            email_sent = await email_service.send_security_notification(
                shipment, "activate",
                location=intervention.location,
                notes=intervention.notes
            )
            logger.info(f"✅ Security activation email sent: {email_sent}")
        except Exception as e:
            logger.error(f"❌ Failed to send security activation email: {e}", exc_info=True)
        
    elif intervention.action == "clear":
        shipment.security_hold_active = False
        shipment.security_hold_cleared_at = now
        shipment.current_status = "SECURITY_CLEARED"
        
        # Log intervention
        log = InterventionLog(
            shipment_id=shipment.id,
            intervention_type="security",
            action="clear",
            previous_state=previous_state,
            new_state=False,
            notes=intervention.notes
        )
        db.add(log)
        
        # Send email notification
        try:
            logger.info(f"📧 Sending security clear email for {tracking}")
            email_sent = await email_service.send_security_notification(
                shipment, "clear",
                notes=intervention.notes
            )
            logger.info(f"✅ Security clear email sent: {email_sent}")
        except Exception as e:
            logger.error(f"❌ Failed to send security clear email: {e}", exc_info=True)
    
    # Update shipment
    shipment.status_updated_at = now
    db.commit()
    
    logger.info(f"Security {intervention.action} for {tracking}")
    
    return InterventionResponse(
        success=True,
        intervention_type="security",
        action=intervention.action,
        new_state=shipment.security_hold_active,
        timestamp=now,
        email_sent=email_sent,
        message=f"Security hold {intervention.action}d successfully"
    )

@router.post("/{tracking}/interventions/damage", response_model=InterventionResponse)
async def report_damage(
    tracking: str,
    intervention: DamageIntervention,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Report or resolve damage"""
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
    
    # Record previous state
    previous_state = shipment.damage_reported
    now = datetime.utcnow()
    
    email_sent = False
    
    # Update based on action
    if intervention.action == "report":
        shipment.damage_reported = True
        shipment.damage_reported_at = now
        shipment.damage_description = intervention.description
        shipment.current_status = "DAMAGE_REPORTED"
        
        # Log intervention
        log = InterventionLog(
            shipment_id=shipment.id,
            intervention_type="damage",
            action="report",
            previous_state=previous_state,
            new_state=True,
            notes=intervention.description
        )
        db.add(log)
        
        # Send email notification
        try:
            logger.info(f"📧 Sending damage report email for {tracking}")
            email_sent = await email_service.send_damage_notification(
                shipment, "report", description=intervention.description
            )
            logger.info(f"✅ Damage report email sent: {email_sent}")
        except Exception as e:
            logger.error(f"❌ Failed to send damage report email: {e}", exc_info=True)
        
    elif intervention.action == "resolve":
        shipment.damage_reported = False
        shipment.damage_resolved_at = now
        shipment.damage_resolution_notes = intervention.resolution_notes
        shipment.current_status = "DAMAGE_RESOLVED"
        
        # Log intervention
        log = InterventionLog(
            shipment_id=shipment.id,
            intervention_type="damage",
            action="resolve",
            previous_state=previous_state,
            new_state=False,
            notes=intervention.resolution_notes
        )
        db.add(log)
        
        # Send email notification
        try:
            logger.info(f"📧 Sending damage resolve email for {tracking}")
            email_sent = await email_service.send_damage_notification(
                shipment, "resolve", resolution=intervention.resolution_notes
            )
            logger.info(f"✅ Damage resolve email sent: {email_sent}")
        except Exception as e:
            logger.error(f"❌ Failed to send damage resolve email: {e}", exc_info=True)
    
    # Update shipment
    shipment.status_updated_at = now
    db.commit()
    
    logger.info(f"Damage {intervention.action} for {tracking}")
    
    return InterventionResponse(
        success=True,
        intervention_type="damage",
        action=intervention.action,
        new_state=shipment.damage_reported,
        timestamp=now,
        email_sent=email_sent,
        message=f"Damage {intervention.action}ed successfully"
    )

@router.post("/{tracking}/interventions/return", response_model=InterventionResponse)
async def initiate_return(
    tracking: str,
    intervention: ReturnIntervention,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Initiate return to sender"""
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
    
    # Record previous state
    previous_state = shipment.return_active
    now = datetime.utcnow()
    
    email_sent = False
    
    # Update based on action
    if intervention.action == "initiate":
        shipment.return_active = True
        shipment.return_initiated_at = now
        shipment.return_reason = intervention.reason
        shipment.current_status = "RETURN_TO_SENDER"
        
        # Log intervention
        log = InterventionLog(
            shipment_id=shipment.id,
            intervention_type="return",
            action="initiate",
            previous_state=previous_state,
            new_state=True,
            notes=intervention.reason
        )
        db.add(log)
        
        # Send email notification
        try:
            logger.info(f"📧 Sending return initiation email for {tracking}")
            email_sent = await email_service.send_return_notification(
                shipment, reason=intervention.reason
            )
            logger.info(f"✅ Return initiation email sent: {email_sent}")
        except Exception as e:
            logger.error(f"❌ Failed to send return email: {e}", exc_info=True)
    
    # Update shipment
    shipment.status_updated_at = now
    db.commit()
    
    logger.info(f"Return initiated for {tracking}")
    
    return InterventionResponse(
        success=True,
        intervention_type="return",
        action=intervention.action,
        new_state=shipment.return_active,
        timestamp=now,
        email_sent=email_sent,
        message="Return to sender initiated successfully"
    )

@router.post("/{tracking}/interventions/delay", response_model=InterventionResponse)
async def report_delay(
    tracking: str,
    intervention: DelayIntervention,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Report or resolve delay"""
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
    
    # Record previous state
    previous_state = shipment.delay_active
    now = datetime.utcnow()
    
    email_sent = False
    
    # Update based on action
    if intervention.action == "report":
        shipment.delay_active = True
        shipment.delay_reported_at = now
        shipment.delay_reason = intervention.reason
        shipment.delay_notes = intervention.notes
        shipment.original_eta = shipment.estimated_delivery_date
        if intervention.revised_eta:
            shipment.revised_eta = intervention.revised_eta
        shipment.current_status = "TRANSIT_EXCEPTION"
        
        # Log intervention
        log = InterventionLog(
            shipment_id=shipment.id,
            intervention_type="delay",
            action="report",
            previous_state=previous_state,
            new_state=True,
            notes=intervention.notes
        )
        db.add(log)
        
        # Send email notification
        try:
            logger.info(f"📧 Sending delay report email for {tracking}")
            email_sent = await email_service.send_delay_notification(
                shipment, "report", 
                reason=intervention.reason,
                revised_eta=intervention.revised_eta.isoformat() if intervention.revised_eta else None
            )
            logger.info(f"✅ Delay report email sent: {email_sent}")
        except Exception as e:
            logger.error(f"❌ Failed to send delay report email: {e}", exc_info=True)
        
    elif intervention.action == "resolve":
        shipment.delay_active = False
        shipment.delay_resolved_at = now
        
        # Log intervention
        log = InterventionLog(
            shipment_id=shipment.id,
            intervention_type="delay",
            action="resolve",
            previous_state=previous_state,
            new_state=False,
            notes=intervention.notes
        )
        db.add(log)
        
        # Send email notification
        try:
            logger.info(f"📧 Sending delay resolve email for {tracking}")
            email_sent = await email_service.send_delay_notification(
                shipment, "resolve"
            )
            logger.info(f"✅ Delay resolve email sent: {email_sent}")
        except Exception as e:
            logger.error(f"❌ Failed to send delay resolve email: {e}", exc_info=True)
    
    # Update shipment
    shipment.status_updated_at = now
    db.commit()
    
    logger.info(f"Delay {intervention.action} for {tracking}")
    
    return InterventionResponse(
        success=True,
        intervention_type="delay",
        action=intervention.action,
        new_state=shipment.delay_active,
        timestamp=now,
        email_sent=email_sent,
        message=f"Delay {intervention.action}ed successfully"
    )