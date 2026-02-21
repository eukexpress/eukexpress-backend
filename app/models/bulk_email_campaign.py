# Eukexpress\backend\app\models\bulk_email_campaign.py
"""
Bulk Email Campaign Model
Track mass email communications
"""

from sqlalchemy import Column, String, DateTime, Integer, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.database import Base

class BulkEmailCampaign(Base):
    __tablename__ = "bulk_email_campaigns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_name = Column(String(255))
    recipient_filter = Column(String(50))  # 'all', 'customs', 'delayed', 'international'
    subject = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    recipient_count = Column(Integer)
    sent_by = Column(UUID(as_uuid=True), ForeignKey("admin.id"))
    status = Column(String(20), default='PENDING')  # 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED'
    error_message = Column(Text)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)