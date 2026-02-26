"""
Heritage Trust Email API Endpoints
Simple email sender with just the basics
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, status
from typing import Optional, List
import os
import tempfile
import logging
from datetime import datetime
import traceback

from app.services.heritage_email_service import heritage_email
from app.database import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(tags=["Heritage Trust Email"])
logger = logging.getLogger(__name__)

# Simple response model
class EmailResponse:
    def __init__(self, success: bool, message: str, message_id: str = None):
        self.success = success
        self.message = message
        self.message_id = message_id

@router.post("/send")
async def send_email(
    to: str = Form(..., description="Recipient email address(es), comma-separated"),
    subject: str = Form(..., description="Email subject"),
    html_content: Optional[str] = Form(None, description="HTML content of email"),
    text_content: Optional[str] = Form(None, description="Plain text version"),
    attachments: Optional[List[UploadFile]] = File(None)
):
    """
    Simple email sender - Just send emails, nothing fancy
    """
    logger.info(f"=== Sending Email ===")
    logger.info(f"To: {to}")
    logger.info(f"Subject: {subject}")
    
    temp_files = []
    
    try:
        # Basic validation
        if not to:
            raise HTTPException(status_code=422, detail="Recipient email is required")
        
        if not subject:
            raise HTTPException(status_code=422, detail="Subject is required")
        
        # Parse recipients
        recipients = [email.strip() for email in to.split(',') if email.strip()]
        
        # Process attachments if any
        attachment_list = []
        if attachments:
            for file in attachments:
                if file and file.filename:
                    # Save temp file
                    content = await file.read()
                    suffix = os.path.splitext(file.filename)[1]
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                        temp_file.write(content)
                        temp_file.flush()
                        attachment_list.append({
                            'path': temp_file.name,
                            'filename': file.filename
                        })
                        temp_files.append(temp_file.name)
        
        # Send email
        result = heritage_email.send_email(
            to=recipients,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attachments=attachment_list if attachment_list else None
        )
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Email sent successfully",
                "message_id": result.get('message_id'),
                "from_email": heritage_email.from_email
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to send email'))
            
    except HTTPException:
        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        raise
    except Exception as e:
        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def send_test_email(
    to: str = Form(..., description="Email address to send test to")
):
    """Send a simple test email"""
    try:
        result = heritage_email.send_test_email(to)
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Test email sent",
                "message_id": result.get('message_id'),
                "from_email": heritage_email.from_email
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Failed to send test email'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ping")
async def ping():
    """Check if service is running"""
    return {
        "status": "ok",
        "message": "Heritage Trust email service is running",
        "from_email": heritage_email.from_email,
        "from_name": heritage_email.from_name
    }