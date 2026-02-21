# Eukexpress\backend\app\schemas\status.py
"""
Status History Pydantic Schemas
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class StatusHistoryBase(BaseModel):
    shipment_id: uuid.UUID
    previous_status: Optional[str]
    new_status: str
    changed_by: str = "admin"
    location: Optional[str]
    notes: Optional[str]

class StatusHistoryCreate(StatusHistoryBase):
    pass

class StatusHistoryResponse(StatusHistoryBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class StatusUpdate(BaseModel):
    status: str
    location: Optional[str] = None
    notes: Optional[str] = None

class AvailableStatuses(BaseModel):
    current: str
    current_display: str
    available: list
    available_display: list
    requires_customs: bool
    