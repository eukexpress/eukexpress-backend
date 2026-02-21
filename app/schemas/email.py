# Eukexpress\backend\app\schemas\email.py
"""
Email Communication Schemas
Request and response models for email operations
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Direct Message
class DirectMessage(BaseModel):
    recipient: str = Field(..., pattern=r"^(sender|recipient|both)$", description="recipient type: sender, recipient, or both")
    subject: str = Field(..., min_length=1, max_length=500)
    message: str = Field(..., min_length=1)
    include_tracking_link: bool = True

# Email Resend
class EmailResend(BaseModel):
    email_type: str = Field(..., pattern=r"^(invoice|last_notification)$", description="type of email to resend")
    recipient: str = Field(..., pattern=r"^(sender|recipient)$", description="recipient for resend")

# Bulk Email Campaign
class BulkEmailCampaign(BaseModel):
    filter: str = Field(..., pattern=r"^(all|customs_bond|delayed|international|active)$", description="filter for bulk email")
    subject: str = Field(..., min_length=1, max_length=500)
    message: str = Field(..., min_length=1)
    include_tracking_links: bool = True

# Email History Item
class EmailHistoryItem(BaseModel):
    timestamp: datetime
    type: str
    recipient: str
    recipient_email: str
    subject: str
    status: str
    message_id: Optional[str] = None

# Campaign Response
class CampaignResponse(BaseModel):
    success: bool
    campaign_id: str
    recipient_count: int
    estimated_completion: datetime