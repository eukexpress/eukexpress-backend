# Eukexpress\backend\app\schemas\shipment.py
"""
Shipment Pydantic Schemas
Request and response models for shipment operations
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal
import uuid

# Base Shipment Schema
class ShipmentBase(BaseModel):
    tracking_number: str
    invoice_number: str
    sender_name: str
    sender_email: EmailStr
    sender_phone: str
    sender_address: str
    recipient_name: str
    recipient_email: EmailStr
    recipient_phone: str
    recipient_address: str
    origin_location: str
    origin_code: Optional[str] = None
    destination_location: str
    destination_code: Optional[str] = None
    goods_description: str
    weight_kg: Optional[Decimal] = None
    dimensions: Optional[Dict[str, float]] = None
    declared_value: Optional[Decimal] = None
    declared_currency: str = "USD"
    shipping_amount: Decimal
    payment_currency: str = "NGN"
    payment_method: Optional[str] = None
    payment_status: str = "PENDING"
    sending_date: date
    estimated_delivery_date: date
    is_international: bool = False

# Schema for creating a new shipment
class ShipmentCreate(BaseModel):
    sender_name: str = Field(..., min_length=2, max_length=255)
    sender_email: EmailStr
    sender_phone: str = Field(..., min_length=5, max_length=50)
    sender_address: str = Field(..., min_length=5)
    recipient_name: str = Field(..., min_length=2, max_length=255)
    recipient_email: EmailStr
    recipient_phone: str = Field(..., min_length=5, max_length=50)
    recipient_address: str = Field(..., min_length=5)
    origin_location: str = Field(..., min_length=2)
    destination_location: str = Field(..., min_length=2)
    goods_description: str = Field(..., min_length=3)
    weight_kg: Optional[Decimal] = Field(None, gt=0)
    dimensions: Optional[Dict[str, float]] = None
    declared_value: Optional[Decimal] = Field(None, gt=0)
    shipping_amount: Decimal = Field(..., gt=0)
    payment_method: Optional[str] = None
    payment_status: str = "PENDING"
    sending_date: date
    estimated_delivery_date: date
    
    @validator('estimated_delivery_date')
    def validate_dates(cls, v, values):
        if 'sending_date' in values and v < values['sending_date']:
            raise ValueError('Estimated delivery date must be after sending date')
        return v

# Schema for shipment response
class ShipmentResponse(ShipmentBase):
    id: uuid.UUID
    front_image_path: str
    rear_image_path: str
    qr_code_path: Optional[str] = None
    invoice_pdf_path: Optional[str] = None
    current_status: str
    current_location: Optional[str] = None
    status_updated_at: datetime
    customs_bond_active: bool = False
    security_hold_active: bool = False
    damage_reported: bool = False
    return_active: bool = False
    delay_active: bool = False
    actual_delivery_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# Schema for shipment list item (lightweight)
class ShipmentListItem(BaseModel):
    tracking_number: str
    status: str
    status_display: str
    status_color: str
    origin_location: str
    destination_location: str
    sender_name: str
    recipient_name: str
    last_update: datetime
    has_interventions: bool
    intervention_types: List[str] = []
    
    class Config:
        from_attributes = True

# Schema for status update
class StatusUpdate(BaseModel):
    status: str
    location: Optional[str] = None
    notes: Optional[str] = None

# Schema for shipment timeline item
class TimelineItem(BaseModel):
    timestamp: datetime
    event: str
    display: str
    location: Optional[str] = None
    notes: Optional[str] = None
    type: str  # 'status', 'intervention', 'system'