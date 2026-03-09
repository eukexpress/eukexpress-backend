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

# Schema for creating a new shipment (with auto-generated tracking)
class ShipmentCreateRequest(BaseModel):
    sender_name: str = Field(..., min_length=2, max_length=255)
    sender_email: EmailStr
    sender_phone: str = Field(..., min_length=5, max_length=50)
    sender_address: str = Field(..., min_length=5)
    recipient_name: str = Field(..., min_length=2, max_length=255)
    recipient_email: EmailStr
    recipient_phone: str = Field(..., min_length=5, max_length=50)
    recipient_address: str = Field(..., min_length=5)
    origin_location: str = Field(..., min_length=2)
    origin_code: Optional[str] = Field(None, max_length=10)
    destination_location: str = Field(..., min_length=2)
    destination_code: Optional[str] = Field(None, max_length=10)
    goods_description: str = Field(..., min_length=3)
    weight_kg: Optional[Decimal] = Field(None, gt=0)
    dimensions: Optional[Dict[str, float]] = None
    declared_value: Optional[Decimal] = Field(None, gt=0)
    declared_currency: str = "USD"
    shipping_amount: Decimal = Field(..., gt=0)
    payment_method: Optional[str] = None
    payment_status: str = "PENDING"
    sending_date: date
    estimated_delivery_date: date
    is_international: bool = False
    
    @validator('estimated_delivery_date')
    def validate_dates(cls, v, values):
        if 'sending_date' in values and v < values['sending_date']:
            raise ValueError('Estimated delivery date must be after sending date')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "sender_name": "John Doe",
                "sender_email": "john@example.com",
                "sender_phone": "+1234567890",
                "sender_address": "123 Main St, City",
                "recipient_name": "Jane Smith",
                "recipient_email": "jane@example.com",
                "recipient_phone": "+0987654321",
                "recipient_address": "456 Oak Ave, Town",
                "origin_location": "New York",
                "origin_code": "NYC",
                "destination_location": "London",
                "destination_code": "LHR",
                "goods_description": "Electronics",
                "weight_kg": 5.5,
                "dimensions": {"length": 30, "width": 20, "height": 15},
                "declared_value": 500.00,
                "declared_currency": "USD",
                "shipping_amount": 75.00,
                "payment_method": "CARD",
                "payment_status": "PAID",
                "sending_date": "2026-03-07",
                "estimated_delivery_date": "2026-03-14",
                "is_international": True
            }
        }

# Schema for creating a new shipment (legacy - kept for compatibility)
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
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "tracking_number": "EUK7F9K2",
                "invoice_number": "INV-20260307-1234",
                "sender_name": "John Doe",
                "current_status": "IN_TRANSIT",
                "created_at": "2026-03-07T10:30:00Z"
            }
        }

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
        json_schema_extra = {
            "example": {
                "tracking_number": "EUK7F9K2",
                "status": "IN_TRANSIT",
                "status_display": "In Transit",
                "status_color": "blue",
                "origin_location": "New York",
                "destination_location": "London",
                "sender_name": "John Doe",
                "recipient_name": "Jane Smith",
                "last_update": "2026-03-07T14:30:00Z",
                "has_interventions": False,
                "intervention_types": []
            }
        }

# Schema for status update
class StatusUpdate(BaseModel):
    status: str
    location: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "IN_TRANSIT",
                "location": "New York JFK Airport",
                "notes": "Shipment cleared customs"
            }
        }

# Schema for shipment timeline item
class TimelineItem(BaseModel):
    timestamp: datetime
    event: str
    display: str
    location: Optional[str] = None
    notes: Optional[str] = None
    type: str  # 'status', 'intervention', 'system'
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-03-07T14:30:00Z",
                "event": "STATUS_CHANGE",
                "display": "Status changed to In Transit",
                "location": "New York",
                "notes": "Shipment departed",
                "type": "status"
            }
        }