"""
Heritage Trust Email API Endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, status
from typing import Optional, List
import os
import tempfile
import logging
from datetime import datetime
import traceback

from app.services.heritage_email_service import heritage_email

router = APIRouter(tags=["Heritage Trust Email"])
logger = logging.getLogger(__name__)

@router.post("/send", status_code=status.HTTP_200_OK)
async def send_email(
    request: Request,
    to: str = Form(..., description="Recipient email address(es), comma-separated"),
    subject: str = Form(..., description="Email subject"),
    html_content: Optional[str] = Form("", description="HTML version of email"),
    text_content: Optional[str] = Form("", description="Plain text version"),
    attachments: Optional[List[UploadFile]] = File(None, description="Optional file attachments")
):
    logger.info(f"Received send email request to: {to}")
    
    if not to or not to.strip():
        raise HTTPException(status_code=400, detail="'to' field is required")
    
    if not subject or not subject.strip():
        raise HTTPException(status_code=400, detail="'subject' field is required")
    
    recipients = [email.strip() for email in to.split(',') if email.strip()]
    if not recipients:
        raise HTTPException(status_code=400, detail="At least one valid recipient email is required")
    
    if not html_content and not text_content:
        text_content = " "
    
    attachment_list = []
    temp_files = []
    
    if attachments:
        for file in attachments:
            if file.filename:
                content = await file.read()
                if len(content) > 10 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail=f"File {file.filename} exceeds 10MB limit")
                
                suffix = os.path.splitext(file.filename)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_file.write(content)
                    temp_file.flush()
                    attachment_list.append({
                        'path': temp_file.name,
                        'filename': file.filename,
                        'content_type': file.content_type
                    })
                    temp_files.append(temp_file.name)
    
    try:
        result = heritage_email.send_email(
            to=recipients,
            subject=subject,
            html_content=html_content if html_content else None,
            text_content=text_content if text_content else None,
            attachments=attachment_list
        )
        
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
                "from": heritage_email.from_email
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
            
    except Exception as e:
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test", status_code=status.HTTP_200_OK)
async def send_test_email(to: str = Form(..., description="Email address to send test to")):
    logger.info(f"Received test email request to: {to}")
    
    if not to or '@' not in to:
        raise HTTPException(status_code=400, detail="Valid email address required")
    
    try:
        result = heritage_email.send_test_email(to)
        if result.get('success'):
            return {
                "success": True, 
                "message": "Test email sent", 
                "message_id": result.get('message_id'),
                "from": heritage_email.from_email
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invoice", status_code=status.HTTP_200_OK)
async def send_invoice(
    to: str = Form(..., description="Recipient email address"),
    invoice_number: str = Form(..., description="Invoice number"),
    amount: float = Form(..., description="Invoice amount", gt=0),
    description: str = Form(..., description="Invoice description"),
    pdf_attachment: Optional[UploadFile] = File(None, description="PDF invoice attachment")
):
    logger.info(f"Received invoice request to: {to}, invoice: {invoice_number}")
    
    if not to or '@' not in to:
        raise HTTPException(status_code=400, detail="Valid email address required")
    
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    invoice_data = {
        'invoice_number': invoice_number,
        'amount': f"{amount:.2f}",
        'description': description,
        'date': datetime.now().strftime("%Y-%m-%d")
    }
    
    pdf_path = None
    if pdf_attachment and pdf_attachment.filename:
        if not pdf_attachment.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Attachment must be a PDF file")
        
        content = await pdf_attachment.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="PDF file exceeds 10MB limit")
        
        suffix = os.path.splitext(pdf_attachment.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_file.flush()
            pdf_path = temp_file.name
    
    try:
        result = heritage_email.send_invoice(
            to_email=to,
            invoice_data=invoice_data,
            pdf_path=pdf_path
        )
        
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except:
                pass
        
        if result.get('success'):
            return {
                "success": True, 
                "message": "Invoice sent", 
                "message_id": result.get('message_id'),
                "from": heritage_email.from_email
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
            
    except Exception as e:
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    return {
        "status": "ok", 
        "message": "Heritage Trust email service is running",
        "from_email": heritage_email.from_email,
        "from_name": heritage_email.from_name
    }