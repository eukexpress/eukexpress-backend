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
    # Log all received form data for debugging
    logger.info("=" * 50)
    logger.info("HERITAGE EMAIL SEND ENDPOINT CALLED")
    logger.info("=" * 50)
    
    # Log raw form data
    try:
        form_data = await request.form()
        logger.info(f"Raw form keys received: {list(form_data.keys())}")
        for key in form_data.keys():
            if key != 'attachments':
                logger.info(f"Field '{key}': '{form_data.get(key)}'")
    except Exception as e:
        logger.error(f"Error reading form data: {e}")
    
    logger.info(f"to: '{to}'")
    logger.info(f"subject: '{subject}'")
    logger.info(f"html_content: '{html_content[:50]}...' (length: {len(html_content)})" if html_content else "html_content: empty")
    logger.info(f"text_content: '{text_content[:50]}...' (length: {len(text_content)})" if text_content else "text_content: empty")
    logger.info(f"attachments count: {len(attachments) if attachments else 0}")
    
    # Validate inputs
    if not to or not to.strip():
        logger.error("Validation failed: 'to' field is empty")
        raise HTTPException(status_code=400, detail="'to' field is required")
    
    if not subject or not subject.strip():
        logger.error("Validation failed: 'subject' field is empty")
        raise HTTPException(status_code=400, detail="'subject' field is required")
    
    # Parse recipients
    recipients = [email.strip() for email in to.split(',') if email.strip()]
    logger.info(f"Parsed recipients: {recipients}")
    
    if not recipients:
        logger.error("Validation failed: No valid recipients")
        raise HTTPException(status_code=400, detail="At least one valid recipient email is required")
    
    # Validate email format (basic check)
    for recipient in recipients:
        if '@' not in recipient or '.' not in recipient:
            logger.warning(f"Potentially invalid email format: {recipient}")
    
    # Ensure at least one content type is provided
    if not html_content and not text_content:
        logger.info("No content provided, using empty text fallback")
        text_content = " "
    
    attachment_list = []
    temp_files = []
    
    if attachments:
        for file in attachments:
            if file.filename:
                logger.info(f"Processing attachment: {file.filename} (size: {file.size if hasattr(file, 'size') else 'unknown'})")
                
                content = await file.read()
                file_size = len(content)
                logger.info(f"Attachment size: {file_size} bytes")
                
                if file_size > 10 * 1024 * 1024:
                    logger.error(f"File too large: {file_size} bytes")
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
                    logger.info(f"Saved temp file: {temp_file.name}")
    
    try:
        logger.info("Calling heritage_email.send_email...")
        logger.info(f"Parameters - to: {recipients}, subject: {subject}")
        logger.info(f"html_content provided: {bool(html_content)}, text_content provided: {bool(text_content)}")
        logger.info(f"attachments count: {len(attachment_list)}")
        
        result = heritage_email.send_email(
            to=recipients,
            subject=subject,
            html_content=html_content if html_content else None,
            text_content=text_content if text_content else None,
            attachments=attachment_list
        )
        
        logger.info(f"send_email result: {result}")
        
        # Clean up temp files
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
                logger.info(f"Cleaned up: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_file}: {e}")
        
        if result.get('success'):
            logger.info(f"Email sent successfully! Message ID: {result.get('message_id')}")
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
        logger.error(f"Exception in send_email: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Clean up temp files on error
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test", status_code=status.HTTP_200_OK)
async def send_test_email(to: str = Form(..., description="Email address to send test to")):
    logger.info("=" * 50)
    logger.info("HERITAGE TEST EMAIL ENDPOINT CALLED")
    logger.info("=" * 50)
    logger.info(f"Received test email request to: '{to}'")
    
    if not to or '@' not in to:
        logger.error(f"Invalid email address: '{to}'")
        raise HTTPException(status_code=400, detail="Valid email address required")
    
    try:
        logger.info(f"Sending test email to {to}")
        result = heritage_email.send_test_email(to)
        logger.info(f"send_test_email result: {result}")
        
        if result.get('success'):
            logger.info(f"Test email sent successfully! Message ID: {result.get('message_id')}")
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
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/invoice", status_code=status.HTTP_200_OK)
async def send_invoice(
    to: str = Form(..., description="Recipient email address"),
    invoice_number: str = Form(..., description="Invoice number"),
    amount: float = Form(..., description="Invoice amount", gt=0),
    description: str = Form(..., description="Invoice description"),
    pdf_attachment: Optional[UploadFile] = File(None, description="PDF invoice attachment")
):
    logger.info("=" * 50)
    logger.info("HERITAGE INVOICE EMAIL ENDPOINT CALLED")
    logger.info("=" * 50)
    logger.info(f"Received invoice request to: {to}, invoice: {invoice_number}, amount: {amount}")
    
    if not to or '@' not in to:
        logger.error(f"Invalid email address: {to}")
        raise HTTPException(status_code=400, detail="Valid email address required")
    
    if amount <= 0:
        logger.error(f"Invalid amount: {amount}")
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    invoice_data = {
        'invoice_number': invoice_number,
        'amount': f"{amount:.2f}",
        'description': description,
        'date': datetime.now().strftime("%Y-%m-%d")
    }
    logger.info(f"Invoice data: {invoice_data}")
    
    pdf_path = None
    if pdf_attachment and pdf_attachment.filename:
        logger.info(f"Processing PDF attachment: {pdf_attachment.filename}")
        
        if not pdf_attachment.filename.lower().endswith('.pdf'):
            logger.error(f"Invalid file type: {pdf_attachment.filename}")
            raise HTTPException(status_code=400, detail="Attachment must be a PDF file")
        
        content = await pdf_attachment.read()
        file_size = len(content)
        logger.info(f"PDF size: {file_size} bytes")
        
        if file_size > 10 * 1024 * 1024:
            logger.error(f"PDF too large: {file_size} bytes")
            raise HTTPException(status_code=400, detail="PDF file exceeds 10MB limit")
        
        suffix = os.path.splitext(pdf_attachment.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(content)
            temp_file.flush()
            pdf_path = temp_file.name
            logger.info(f"Saved PDF temp file: {pdf_path}")
    
    try:
        logger.info(f"Sending invoice email to {to}")
        result = heritage_email.send_invoice(
            to_email=to,
            invoice_data=invoice_data,
            pdf_path=pdf_path
        )
        logger.info(f"send_invoice result: {result}")
        
        if pdf_path:
            try:
                os.unlink(pdf_path)
                logger.info(f"Cleaned up PDF: {pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up PDF: {e}")
        
        if result.get('success'):
            logger.info(f"Invoice sent successfully! Message ID: {result.get('message_id')}")
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
            
    except Exception as e:
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except:
                pass
        logger.error(f"Invoice sending failed: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ping", status_code=status.HTTP_200_OK)
async def ping():
    logger.info("Heritage Trust ping endpoint called")
    return {
        "status": "ok", 
        "message": "Heritage Trust email service is running",
        "from_email": heritage_email.from_email,
        "from_name": heritage_email.from_name
    }