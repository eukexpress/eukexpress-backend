# Eukexpress\backend\app\models\email_log.py
"""
Email Log Model - Track all email communications
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.database import Base

class EmailLog(Base):
    __tablename__ = "email_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    shipment_id = Column(UUID(as_uuid=True), ForeignKey("shipments.id", ondelete="SET NULL"), nullable=True)
    recipient_type = Column(String(20))  # 'sender', 'recipient', 'both'
    recipient_email = Column(String(255), nullable=False)
    email_type = Column(String(50), nullable=False)  # 'invoice', 'customs_notice', 'delivery_confirmation', 'custom_message'
    subject = Column(String(500), nullable=False)
    message_id = Column(String(255))  # Resend message ID
    status = Column(String(20), default='SENT')  # 'SENT', 'FAILED', 'OPENED'
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    
    # Relationship - Fixed: added missing import
    shipment = relationship("Shipment", back_populates="email_logs")
    
    def __repr__(self):
        return f"<EmailLog {self.recipient_email}: {self.email_type}>"