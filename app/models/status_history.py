# Eukexpress\backend\app\models\status_history.py
"""
Status History Model - Complete audit trail of all status changes
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.database import Base

class StatusHistory(Base):
    __tablename__ = "status_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50))
    new_status = Column(String(50), nullable=False)
    changed_by = Column(String(50), default='admin')  # 'admin' or 'system'
    location = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    # Relationship - Fixed: added missing import and proper reference
    shipment = relationship("Shipment", back_populates="status_history")
    
    def __repr__(self):
        return f"<StatusHistory {self.shipment_id}: {self.previous_status} -> {self.new_status}>"