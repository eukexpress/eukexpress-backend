"""
Heritage Trust Email API Endpoints
Integrated with app.config.settings
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
    subject: str = Form(..., description="Email subject", min_length=1, max_length=255),
    html_content: Optional[str] = Form(None, description="HTML version of email"),
    text_content: Optional[str] = Form(None, description="Plain text version"),
    attachments: Optional[List[UploadFile]] = File(None, description="Optional file attachments")
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
    logger.info(f"Subject: {subject}")
    logger.info(f"HTML content provided: {bool(html_content)}")
    logger.info(f"Text content provided: {bool(text_content)}")
    logger.info(f"Attachments count: {len(attachments) if attachments else 0}")
    
    # Validate inputs
    if not to or not to.strip():
        raise HTTPException(status_code=400, detail="'to' field is required")
    
    if not subject or not subject.strip():
        raise HTTPException(status_code=400, detail="'subject' field is required")
    
    if not html_content and not text_content:
        # At least one content type must be provided
        text_content = " "  # Empty fallback
    
    # Parse recipients
    recipients = [email.strip() for email in to.split(',') if email.strip()]
    if not recipients:
        raise HTTPException(status_code=400, detail="At least one valid recipient email is required")
    
    # Validate email format (basic check)
    for recipient in recipients:
        if '@' not in recipient or '.' not in recipient:
            logger.warning(f"Potentially invalid email format: {recipient}")
    
    # Prepare attachments
    attachment_list = []
    temp_files = []  # Track temp files for cleanup
    
    if attachments:
        for file in attachments:
            if file.filename:
                logger.info(f"Processing attachment: {file.filename} ({file.content_type})")
                
                # Check file size (limit to 10MB)
                file_size = 0
                content = await file.read()
                file_size = len(content)
                
                if file_size > 10 * 1024 * 1024:  # 10MB limit
                    logger.warning(f"File too large: {file.filename} ({file_size} bytes)")
                    raise HTTPException(status_code=400, detail=f"File {file.filename} exceeds 10MB limit")
                
                # Save uploaded file temporarily
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
                    logger.info(f"Saved temp file: {temp_file.name}")
    
    try:
        # Send email
        logger.info(f"Calling heritage_email.send_email with {len(recipients)} recipients")
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
            logger.info(f"Email sent successfully: {result.get('message_id')}")
            return {
                "success": True,
                "message": "Email sent successfully",
                "message_id": result.get('message_id'),
                "from": heritage_email.from_email
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"Email sending failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        # Re-raise HTTP exceptions
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        raise
    except Exception as e:
        # Clean up temp files on error
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        logger.error(f"Exception in send_email: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test", status_code=status.HTTP_200_OK)
async def send_test_email(to: str = Form(..., description="Email address to send test to")):
    """Send a test email to verify configuration"""
    logger.info(f"Received test email request to: {to}")
    
    if not to or '@' not in to:
        raise HTTPException(status_code=400, detail="Valid email address required")
    
    try:
        result = heritage_email.send_test_email(to)
        if result.get('success'):
            logger.info(f"Test email sent: {result.get('message_id')}")
            return {
                "success": True, 
                "message": "Test email sent", 
                "message_id": result.get('message_id'),
                "from": heritage_email.from_email
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"Test email failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
    except Exception as e:
        logger.error(f"Exception in send_test_email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invoice", status_code=status.HTTP_200_OK)
async def send_invoice(
    to: str = Form(..., description="Recipient email address"),
    invoice_number: str = Form(..., description="Invoice number"),
    amount: float = Form(..., description="Invoice amount", gt=0),
    description: str = Form(..., description="Invoice description"),
    pdf_attachment: Optional[UploadFile] = File(None, description="PDF invoice attachment")
):
    """Send invoice email with optional PDF"""
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
    
    # Handle PDF attachment
    pdf_path = None
    if pdf_attachment and pdf_attachment.filename:
        logger.info(f"Processing PDF attachment: {pdf_attachment.filename}")
        
        # Check file type
        if not pdf_attachment.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Attachment must be a PDF file")
        
        # Check file size
        content = await pdf_attachment.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB limit
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
        
        # Clean up
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except:
                pass
        
        if result.get('success'):
            logger.info(f"Invoice sent: {result.get('message_id')}")
            return {
                "success": True, 
                "message": "Invoice sent", 
                "message_id": result.get('message_id'),
                "from": heritage_email.from_email
            }
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.error(f"Invoice sending failed: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
            
    except HTTPException:
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except:
                pass
        raise
    except Exception as e:
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except:
                pass
        logger.error(f"Invoice sending failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    """Simple ping endpoint to test if the router is working"""
    return {
        "status": "ok", 
        "message": "Heritage Trust email service is running",
        "from_email": heritage_email.from_email,
        "from_name": heritage_email.from_name
    }