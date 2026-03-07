"""
EukExpress Email API Endpoints
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form, Request
from typing import List, Optional
from pydantic import BaseModel, EmailStr

from app.services.email_service import email_service
from app.api.v1.auth import oauth2_scheme
from app.services import auth_service

router = APIRouter(tags=["Email"])
logger = logging.getLogger(__name__)

class EmailRequest(BaseModel):
    to: List[EmailStr]
    subject: str
    html_content: str
    text_content: Optional[str] = None

class TestEmailRequest(BaseModel):
    to: EmailStr

@router.post("/send")
async def send_email(
    request: EmailRequest,
    token: str = Depends(oauth2_scheme)
):
    """Send an email"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
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

@router.post("/test")
async def send_test_email(
    request: TestEmailRequest,
    token: str = Depends(oauth2_scheme)
):
    """Send a test email"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        result = email_service.send_test_email(request.to)
        
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

@router.get("/ping")
async def ping():
    """Health check for email service"""
    return {
        "success": True,
        "data": {
            "status": "ok",
            "service": "EukExpress Email Service",
            "from_email": email_service.from_email,
            "from_name": email_service.from_name
        }
    }

@router.post("/invoice")
async def send_invoice(
    request: Request,
    to: EmailStr = Form(...),
    invoice_number: str = Form(...),
    amount: str = Form(...),
    description: str = Form(...),
    pdf: UploadFile = File(...),
    token: str = Depends(oauth2_scheme)
):
    """Send an invoice email with PDF attachment"""
    # Verify authentication
    payload = auth_service.decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    try:
        # Read PDF content
        pdf_content = await pdf.read()
        
        # Create HTML content
        html_content = f"""
        <h2>Invoice {invoice_number}</h2>
        <p>Amount: {amount}</p>
        <p>Description: {description}</p>
        <p>Please find your invoice attached.</p>
        """
        
        # Send email with attachment
        result = email_service.send_email(
            to=[to],
            subject=f"Invoice {invoice_number}",
            html_content=html_content,
            attachments=[{
                "filename": pdf.filename,
                "content": pdf_content,
                "content_type": pdf.content_type
            }]
        )
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Invoice sent successfully",
                "id": result.get('id')
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
    
    except Exception as e:
        logger.error(f"Error sending invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))
