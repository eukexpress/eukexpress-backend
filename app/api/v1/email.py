#app/api/v1/email.py
"""
EukExpress Email API Endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.services.email_service import email_service
from app.api.deps import get_current_user_required

router = APIRouter(tags=["Email"])
logger = logging.getLogger(__name__)

class TestEmailRequest(BaseModel):
    to: EmailStr  # Single email for test

class SendEmailRequest(BaseModel):
    to: List[EmailStr]  # Multiple recipients for send
    subject: str
    html_content: str
    text_content: Optional[str] = None

@router.post("/test")
async def send_test_email(
    request: TestEmailRequest,
    current_user = Depends(get_current_user_required)
):
    """Send a test email - expects JSON with single 'to' field"""
    try:
        result = email_service.send_test_email(str(request.to))
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Test email sent successfully",
                "id": result.get('id'),
                "from_email": email_service.from_email
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
    
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    current_user = Depends(get_current_user_required)
):
    """Send an email - expects JSON with multiple recipients"""
    try:
        result = email_service.send_email(
            to=request.to,
            subject=request.subject,
            html_content=request.html_content,
            text_content=request.text_content
        )
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Email sent successfully",
                "id": result.get('id'),
                "from_email": email_service.from_email
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
    
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ping")
async def ping():
    """Health check for email service"""
    return {
        "success": True,
        "data": {
            "status": "ok",
            "service": "EukExpress Email Service",
            "from_email": email_service.from_email,
            "from_name": email_service.from_name,
            "domain": "delivery.eukexpress.com (verified)"
        }
    }

email_router = router