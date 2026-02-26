"""
Heritage Trust Email Schemas
Pydantic models for request/response validation
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# Request Schemas
class HeritageEmailSendRequest(BaseModel):
    """Schema for sending email request"""
    to: str = Field(..., description="Recipient email address(es), comma-separated")
    subject: str = Field(..., description="Email subject", min_length=1, max_length=255)
    html_content: Optional[str] = Field(None, description="HTML version of email")
    text_content: Optional[str] = Field(None, description="Plain text version")
    
    @field_validator('to')
    @classmethod
    def validate_to(cls, v: str) -> str:
        """Validate email addresses"""
        if not v or not v.strip():
            raise ValueError('At least one recipient email is required')
        
        emails = [email.strip() for email in v.split(',') if email.strip()]
        if not emails:
            raise ValueError('At least one valid recipient email is required')
        
        # Basic email validation
        for email in emails:
            if '@' not in email or '.' not in email:
                raise ValueError(f'Invalid email format: {email}')
        
        return v
    
    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v: str) -> str:
        """Validate subject"""
        if not v or not v.strip():
            raise ValueError('Subject is required')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "to": "recipient@example.com",
                "subject": "Test Email",
                "html_content": "<h1>Hello</h1>",
                "text_content": "Hello"
            }
        }

class HeritageTestEmailRequest(BaseModel):
    """Schema for test email request"""
    to: EmailStr = Field(..., description="Email address to send test to")
    
    class Config:
        json_schema_extra = {
            "example": {
                "to": "test@example.com"
            }
        }

class HeritageInvoiceRequest(BaseModel):
    """Schema for invoice email request"""
    to: EmailStr = Field(..., description="Recipient email address")
    invoice_number: str = Field(..., description="Invoice number", min_length=1)
    amount: float = Field(..., description="Invoice amount", gt=0)
    description: str = Field(..., description="Invoice description", min_length=1)
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: float) -> float:
        """Validate amount"""
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return round(v, 2)
    
    class Config:
        json_schema_extra = {
            "example": {
                "to": "client@example.com",
                "invoice_number": "INV-2024-001",
                "amount": 1500.00,
                "description": "Logistics Services - March 2024"
            }
        }

# Response Schemas
class HeritageEmailResponse(BaseModel):
    """Schema for email send response"""
    success: bool = Field(..., description="Whether the email was sent successfully")
    message: str = Field(..., description="Response message")
    message_id: Optional[str] = Field(None, description="Resend message ID if successful")
    from_email: Optional[str] = Field(None, description="From email address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Email sent successfully",
                "message_id": "resend-msg-123",
                "from_email": "onboarding@support.heritagetrust.eukexpress.com"
            }
        }

class HeritagePingResponse(BaseModel):
    """Schema for ping response"""
    status: str = Field(..., description="Service status")
    message: str = Field(..., description="Status message")
    from_email: str = Field(..., description="From email address configured")
    from_name: str = Field(..., description="From name configured")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "message": "Heritage Trust email service is running",
                "from_email": "onboarding@support.heritagetrust.eukexpress.com",
                "from_name": "Heritage Trust"
            }
        }

class HeritageLogEntry(BaseModel):
    """Schema for heritage email log entry"""
    id: str
    message_id: Optional[str]
    to_emails: str
    subject: str
    email_type: str
    status: str
    attachments_count: int
    invoice_number: Optional[str]
    invoice_amount: Optional[float]
    error_message: Optional[str]
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class HeritageLogsResponse(BaseModel):
    """Schema for logs response"""
    total: int
    logs: List[HeritageLogEntry]

# Error Response Schema
class HeritageErrorResponse(BaseModel):
    """Schema for error response"""
    detail: str = Field(..., description="Error detail")
    errors: Optional[Dict[str, List[str]]] = Field(None, description="Validation errors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Validation error",
                "errors": {
                    "to": ["Invalid email format"],
                    "subject": ["Field required"]
                }
            }
        }