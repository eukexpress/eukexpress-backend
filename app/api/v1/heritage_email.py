"""
Heritage Trust Email API Endpoints
Integrated with app.config.settings
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request
from typing import Optional, List
import os
import tempfile
import logging
from datetime import datetime

from app.services.heritage_email_service import heritage_email

# IMPORTANT: Remove the prefix from here - it will be added in main.py
router = APIRouter(tags=["Heritage Trust Email"])
logger = logging.getLogger(__name__)

@router.post("/send")
async def send_email(
    request: Request,
    to: str = Form(...),
    subject: str = Form(...),
    html_content: Optional[str] = Form(None),
    text_content: Optional[str] = Form(None),
    attachments: Optional[List[UploadFile]] = File(None)
):
    """
    Send email through Heritage Trust
    
    - **to**: Recipient email address (comma-separated for multiple)
    - **subject**: Email subject
    - **html_content**: HTML version of email (optional)
    - **text_content**: Plain text version (optional)
    - **attachments**: Optional file attachments (images, PDFs, etc.)
    """
    logger.info(f"Received send email request to: {to}")
    
    # Parse recipients
    recipients = [email.strip() for email in to.split(',')]
    
    # Prepare attachments
    attachment_list = []
    temp_files = []  # Track temp files for cleanup
    
    if attachments:
        for file in attachments:
            if file.filename:
                logger.info(f"Processing attachment: {file.filename}")
                # Save uploaded file temporarily
                suffix = os.path.splitext(file.filename)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    content = await file.read()
                    temp_file.write(content)
                    temp_file.flush()
                    attachment_list.append({
                        'path': temp_file.name,
                        'filename': file.filename
                    })
                    temp_files.append(temp_file.name)
    
    try:
        # Send email
        result = heritage_email.send_email(
            to=recipients,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            attachments=attachment_list
        )
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
                logger.info(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {temp_file}: {e}")
        
        if result.get('success'):
            return {
                "success": True,
                "message": "Email sent successfully",
                "message_id": result.get('message_id')
            }
        else:
            logger.error(f"Email sending failed: {result.get('error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
            
    except Exception as e:
        # Clean up temp files on error
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        logger.error(f"Exception in send_email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def send_test_email(to: str = Form(...)):
    """Send a test email to verify configuration"""
    logger.info(f"Received test email request to: {to}")
    
    result = heritage_email.send_test_email(to)
    if result.get('success'):
        return {"success": True, "message": "Test email sent", "message_id": result.get('message_id')}
    else:
        logger.error(f"Test email failed: {result.get('error')}")
        raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))

@router.post("/invoice")
async def send_invoice(
    to: str = Form(...),
    invoice_number: str = Form(...),
    amount: float = Form(...),
    description: str = Form(...),
    pdf_attachment: Optional[UploadFile] = File(None)
):
    """Send invoice email with optional PDF"""
    logger.info(f"Received invoice request to: {to}, invoice: {invoice_number}")
    
    invoice_data = {
        'invoice_number': invoice_number,
        'amount': f"{amount:.2f}",
        'description': description,
        'date': datetime.now().strftime("%Y-%m-%d")
    }
    
    # Handle PDF attachment
    pdf_path = None
    if pdf_attachment and pdf_attachment.filename:
        logger.info(f"Processing PDF attachment: {pdf_attachment.filename}")
        suffix = os.path.splitext(pdf_attachment.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            content = await pdf_attachment.read()
            temp_file.write(content)
            temp_file.flush()
            pdf_path = temp_file.name
    
    try:
        result = heritage_email.send_invoice(
            to_email=to,
            invoice_data=invoice_data,
            pdf_path=pdf_path
        )
        
        # Clean up
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except:
                pass
        
        if result.get('success'):
            return {"success": True, "message": "Invoice sent", "message_id": result.get('message_id')}
        else:
            raise HTTPException(status_code=500, detail=result.get('error', 'Unknown error'))
            
    except Exception as e:
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except:
                pass
        logger.error(f"Invoice sending failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ping")
async def ping():
    """Simple ping endpoint to test if the router is working"""
    return {"status": "ok", "message": "Heritage Trust email service is running"}