# Eukexpress\backend\app\models\intervention_log.py
"""
Intervention Log Model - Detailed tracking of all toggle actions
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.database import Base

class InterventionLog(Base):
    __tablename__ = "intervention_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False)
    intervention_type = Column(String(50), nullable=False)  # 'customs', 'security', 'damage', 'return', 'delay'
    action = Column(String(20), nullable=False)  # 'activate', 'release', 'report', 'resolve', 'initiate', 'update'
    previous_state = Column(Boolean)
    new_state = Column(Boolean)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationship - Fixed: added missing import
    shipment = relationship("Shipment", back_populates="intervention_logs")
    
    def __repr__(self):
        return f"<InterventionLog {self.shipment_id}: {self.intervention_type} - {self.action}>"