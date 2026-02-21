# Eukexpress\backend\app\schemas\intervention.py
"""
Intervention Pydantic Schemas
Request and response models for intervention operations
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date

# Customs Intervention
class CustomsIntervention(BaseModel):
    action: str = Field(..., pattern=r'^(activate|release)$', description="activate or release")
    location: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None

# Security Intervention
class SecurityIntervention(BaseModel):
    action: str = Field(..., pattern=r'^(activate|clear)$', description="activate or clear")
    location: Optional[str] = None
    notes: Optional[str] = None

# Damage Intervention
class DamageIntervention(BaseModel):
    action: str = Field(..., pattern=r'^(report|resolve)$', description="report or resolve")
    description: Optional[str] = None
    resolution_notes: Optional[str] = None

# Return Intervention
class ReturnIntervention(BaseModel):
    action: str = Field(..., pattern=r'^(initiate)$', description="initiate")
    reason: Optional[str] = None

# Delay Intervention
class DelayIntervention(BaseModel):
    action: str = Field(..., pattern=r'^(report|resolve)$', description="report or resolve")
    reason: Optional[str] = None
    revised_eta: Optional[date] = None
    notes: Optional[str] = None

# Intervention Response
class InterventionResponse(BaseModel):
    success: bool
    intervention_type: str
    action: str
    new_state: bool
    timestamp: datetime
    email_sent: bool = False
    message: Optional[str] = None

# Intervention Status (for shipment detail)
class InterventionStatus(BaseModel):
    customs: dict
    security: dict
    damage: dict
    return_to_sender: dict  
    delay: dict