"""
Heritage Trust Email API Endpoints
Using mandatory onboarding format: onboarding@support.heritagetrust.eukexpress.com
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, status
from typing import Optional, List, Dict, Any
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
    html_content: Optional[str] = Form(None, description="HTML version of email"),
    text_content: Optional[str] = Form(None, description="Plain text version"),
    attachments: Optional[List[UploadFile]] = File(None)
):
    """
    Send email through Heritage Trust using onboarding@ format
    """
    logger.info(f"=== Heritage Trust Send Email Request ===")
    logger.info(f"To: {to}")
    logger.info(f"Subject: {subject}")
    logger.info(f"Has HTML: {bool(html_content)}")
    logger.info(f"Has Text: {bool(text_content)}")
    logger.info(f"Attachments: {len(attachments) if attachments else 0}")
    
    # Parse recipients
    recipients = []
    if to:
        recipients = [email.strip() for email in to.split(',') if email.strip()]
    
    if not recipients:
        raise HTTPException(status_code=400, detail="At least one valid recipient email is required")
    
    # Prepare attachments
    attachment_list = []
    temp_files = []
    
    if attachments:
        for file in attachments:
            if file and file.filename:
                logger.info(f"Processing attachment: {file.filename}")
                try:
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
                        logger.info(f"Saved temp file: {temp_file.name}")
                except Exception as e:
                    logger.error(f"Error processing attachment {file.filename}: {str(e)}")
    
    try:
        # Send email using service
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
                logger.info(f"Cleaned up: {temp_file}")
            except Exception as e:
                logger.warning(f"Cleanup failed for {temp_file}: {e}")
        
        if result.get('success'):
            logger.info(f"✅ Email sent: {result.get('message_id')}")
            return {
                "success": True,
                "message": "Email sent successfully",
                "message_id": result.get('message_id'),
                "from": heritage_email.from_email
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ Send failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        raise
    except Exception as e:
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        logger.error(f"❌ Exception: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test", status_code=status.HTTP_200_OK)
async def send_test_email(
    to: str = Form(..., description="Email address to send test to")
):
    """Send a test email to verify configuration"""
    logger.info(f"=== Heritage Trust Test Email Request ===")
    logger.info(f"To: {to}")
    
    if not to or '@' not in to:
        raise HTTPException(status_code=400, detail="Valid email address required")
    
    try:
        result = heritage_email.send_test_email(to)
        if result.get('success'):
            logger.info(f"✅ Test email sent: {result.get('message_id')}")
            return {
                "success": True,
                "message": "Test email sent",
                "message_id": result.get('message_id'),
                "from": heritage_email.from_email
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ Test failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        logger.error(f"❌ Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invoice", status_code=status.HTTP_200_OK)
async def send_invoice(
    to: str = Form(..., description="Recipient email address"),
    invoice_number: str = Form(..., description="Invoice number"),
    amount: float = Form(..., description="Invoice amount"),
    description: str = Form(..., description="Invoice description"),
    pdf_attachment: Optional[UploadFile] = File(None)
):
    """Send invoice email with optional PDF attachment"""
    logger.info(f"=== Heritage Trust Invoice Request ===")
    logger.info(f"To: {to}, Invoice: {invoice_number}")
    
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
    
    # Handle PDF attachment
    pdf_path = None
    if pdf_attachment and pdf_attachment.filename:
        logger.info(f"Processing PDF: {pdf_attachment.filename}")
        if not pdf_attachment.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Attachment must be a PDF file")
        
        content = await pdf_attachment.read()
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
            logger.info(f"✅ Invoice sent: {result.get('message_id')}")
            return {
                "success": True,
                "message": "Invoice sent",
                "message_id": result.get('message_id'),
                "from": heritage_email.from_email
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"❌ Invoice failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except Exception as e:
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except:
                pass
        logger.error(f"❌ Exception: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    """Test endpoint to verify service is running"""
    return {
        "status": "ok",
        "message": "Heritage Trust email service is running",
        "from_email": heritage_email.from_email,
        "from_name": heritage_email.from_name
    }