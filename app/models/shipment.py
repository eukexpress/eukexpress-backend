# Eukexpress\backend\app\models\shipment.py
"""
Shipment Model - Core shipment records with all tracking data
Complete implementation of the shipment table from the blueprint
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, DECIMAL, JSON, Date, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.database import Base

class Shipment(Base):
    __tablename__ = "shipments"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # TRACKING INFORMATION
    tracking_number = Column(String(8), unique=True, nullable=False, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    
    # SENDER INFORMATION
    sender_name = Column(String(255), nullable=False)
    sender_email = Column(String(255), nullable=False)
    sender_phone = Column(String(50), nullable=False)
    sender_address = Column(Text, nullable=False)
    
    # RECIPIENT INFORMATION
    recipient_name = Column(String(255), nullable=False)
    recipient_email = Column(String(255), nullable=False)
    recipient_phone = Column(String(50), nullable=False)
    recipient_address = Column(Text, nullable=False)
    
    # SHIPMENT DETAILS
    origin_location = Column(String(255), nullable=False)
    origin_code = Column(String(10))
    destination_location = Column(String(255), nullable=False)
    destination_code = Column(String(10))
    goods_description = Column(Text, nullable=False)
    weight_kg = Column(DECIMAL(10, 2))
    dimensions = Column(JSON)  # Format: {"length": 10, "width": 10, "height": 10}
    declared_value = Column(DECIMAL(12, 2))
    declared_currency = Column(String(3), default='USD')
    
    # IMAGES (Exactly 2 - Front and Rear)
    front_image_path = Column(String(500), nullable=False)
    rear_image_path = Column(String(500), nullable=False)
    front_image_hash = Column(String(64), nullable=False)
    rear_image_hash = Column(String(64), nullable=False)
    
    # PAYMENT INFORMATION
    shipping_amount = Column(DECIMAL(12, 2), nullable=False)
    payment_currency = Column(String(3), default='NGN')
    payment_method = Column(String(50))  # 'CASH', 'TRANSFER', 'CARD', 'POS'
    payment_status = Column(String(20), default='PENDING')  # 'PAID', 'PENDING', 'LATER'
    payment_received_at = Column(DateTime(timezone=True))
    
    # DATES
    sending_date = Column(Date, nullable=False)
    estimated_delivery_date = Column(Date, nullable=False)
    actual_delivery_date = Column(Date)
    
    # STATUS
    current_status = Column(String(50), nullable=False, default='BOOKED', index=True)
    current_location = Column(String(255))
    status_updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # INTERNATIONAL FLAG
    is_international = Column(Boolean, default=False)
    
    # =====================================================
    # INTERVENTION TOGGLES
    # =====================================================
    
    # CUSTOMS BOND
    customs_bond_active = Column(Boolean, default=False, index=True)
    customs_bond_activated_at = Column(DateTime(timezone=True))
    customs_bond_released_at = Column(DateTime(timezone=True))
    customs_bond_location = Column(String(255))
    customs_bond_reference = Column(String(100))
    customs_bond_notes = Column(Text)
    
    # SECURITY HOLD
    security_hold_active = Column(Boolean, default=False, index=True)
    security_hold_activated_at = Column(DateTime(timezone=True))
    security_hold_cleared_at = Column(DateTime(timezone=True))
    security_hold_location = Column(String(255))
    security_hold_reference = Column(String(100))
    security_hold_notes = Column(Text)
    
    # CARGO DAMAGE
    damage_reported = Column(Boolean, default=False, index=True)
    damage_reported_at = Column(DateTime(timezone=True))
    damage_resolved_at = Column(DateTime(timezone=True))
    damage_description = Column(Text)
    damage_resolution_notes = Column(Text)
    
    # RETURN TO SENDER
    return_active = Column(Boolean, default=False, index=True)
    return_initiated_at = Column(DateTime(timezone=True))
    return_completed_at = Column(DateTime(timezone=True))
    return_reason = Column(Text)
    
    # DELAY
    delay_active = Column(Boolean, default=False, index=True)
    delay_reported_at = Column(DateTime(timezone=True))
    delay_resolved_at = Column(DateTime(timezone=True))
    delay_reason = Column(Text)
    delay_notes = Column(Text)
    original_eta = Column(Date)
    revised_eta = Column(Date)
    
    # METADATA
    qr_code_path = Column(String(500))
    invoice_pdf_path = Column(String(500))
    created_by_admin = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    status_history = relationship("StatusHistory", back_populates="shipment", cascade="all, delete-orphan")
    intervention_logs = relationship("InterventionLog", back_populates="shipment", cascade="all, delete-orphan")
    email_logs = relationship("EmailLog", back_populates="shipment")
    
    def __repr__(self):
        return f"<Shipment {self.tracking_number}>"