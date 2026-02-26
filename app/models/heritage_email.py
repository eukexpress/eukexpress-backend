"""
Heritage Trust Email Models
Database models for tracking heritage email history
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, JSON, Float
from sqlalchemy.sql import func
from app.database import Base
import uuid

class HeritageEmailLog(Base):
    """Model for tracking heritage trust emails"""
    __tablename__ = "heritage_email_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(255), nullable=True, index=True)
    to_emails = Column(Text, nullable=False)  # JSON array of emails
    subject = Column(String(255), nullable=False)
    email_type = Column(String(50), nullable=False, default="general")  # general, test, invoice
    status = Column(String(50), nullable=False, default="sent")  # sent, failed, bounced
    html_content = Column(Text, nullable=True)
    text_content = Column(Text, nullable=True)
    attachments_count = Column(Integer, default=0)
    
    # Invoice specific fields
    invoice_number = Column(String(100), nullable=True)
    invoice_amount = Column(Float, nullable=True)
    invoice_description = Column(Text, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<HeritageEmailLog {self.id} - {self.subject}>"