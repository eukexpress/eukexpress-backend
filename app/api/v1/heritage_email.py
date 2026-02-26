"""
Heritage Trust Email API Endpoints
Using mandatory onboarding format: onboarding@support.heritagetrust.eukexpress.com
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Request, status, Depends
from typing import Optional, List, Dict, Any
import os
import tempfile
import logging
from datetime import datetime
import traceback
import json

from app.services.heritage_email_service import heritage_email
from app.schemas.heritage import (
    HeritageEmailSendRequest,
    HeritageTestEmailRequest,
    HeritageInvoiceRequest,
    HeritageEmailResponse,
    HeritagePingResponse,
    HeritageErrorResponse,
    HeritageLogsResponse,
    HeritageLogEntry
)
from app.models.heritage_email import HeritageEmailLog
from app.database import SessionLocal
from sqlalchemy.orm import Session

router = APIRouter(tags=["Heritage Trust Email"])
logger = logging.getLogger(__name__)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post(
    "/send", 
    status_code=status.HTTP_200_OK,
    response_model=HeritageEmailResponse,
    responses={
        400: {"model": HeritageErrorResponse},
        422: {"model": HeritageErrorResponse},
        500: {"model": HeritageErrorResponse}
    }
)
async def send_email(
    request: Request,
    to: str = Form(..., description="Recipient email address(es), comma-separated"),
    subject: str = Form(..., description="Email subject"),
    html_content: Optional[str] = Form(None, description="HTML version of email"),
    text_content: Optional[str] = Form(None, description="Plain text version"),
    attachments: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db)
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
    
    temp_files = []
    
    try:
        # Manual validation first to catch issues early
        if not to or not to.strip():
            raise HTTPException(status_code=422, detail="Field 'to' is required")
        
        if not subject or not subject.strip():
            raise HTTPException(status_code=422, detail="Field 'subject' is required")
        
        # Parse recipients
        recipients = [email.strip() for email in to.split(',') if email.strip()]
        if not recipients:
            raise HTTPException(status_code=422, detail="At least one valid recipient email is required")
        
        # Validate email formats
        for email in recipients:
            if '@' not in email or '.' not in email:
                raise HTTPException(status_code=422, detail=f"Invalid email format: {email}")
        
        # Prepare attachments
        attachment_list = []
        
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
        
        # Send email using service
        result = heritage_email.send_email(
            to=recipients,
            subject=subject.strip(),
            html_content=html_content.strip() if html_content else None,
            text_content=text_content.strip() if text_content else None,
            attachments=attachment_list if attachment_list else None
        )
        
        # Create log entry
        email_log = HeritageEmailLog(
            to_emails=to,
            subject=subject,
            email_type="general",
            attachments_count=len(attachment_list),
            html_content=html_content,
            text_content=text_content
        )
        
        if result.get('success'):
            email_log.message_id = result.get('message_id')
            email_log.status = "sent"
            logger.info(f"✅ Email sent: {result.get('message_id')}")
        else:
            email_log.status = "failed"
            email_log.error_message = result.get('error', 'Unknown error')
            logger.error(f"❌ Send failed: {email_log.error_message}")
        
        db.add(email_log)
        db.commit()
        
        if result.get('success'):
            return HeritageEmailResponse(
                success=True,
                message="Email sent successfully",
                message_id=result.get('message_id'),
                from_email=heritage_email.from_email
            )
        else:
            raise HTTPException(status_code=500, detail=email_log.error_message)
            
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
        
        logger.error(f"❌ Exception: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Log error to database
        try:
            error_log = HeritageEmailLog(
                to_emails=to,
                subject=subject,
                email_type="general",
                status="failed",
                error_message=str(e)
            )
            db.add(error_log)
            db.commit()
        except:
            pass
        
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/test", 
    status_code=status.HTTP_200_OK,
    response_model=HeritageEmailResponse
)
async def send_test_email(
    to: str = Form(..., description="Email address to send test to"),
    db: Session = Depends(get_db)
):
    """Send a test email to verify configuration"""
    logger.info(f"=== Heritage Trust Test Email Request ===")
    logger.info(f"To: {to}")
    
    try:
        # Manual validation
        if not to or not to.strip():
            raise HTTPException(status_code=422, detail="Email address is required")
        
        if '@' not in to or '.' not in to:
            raise HTTPException(status_code=422, detail=f"Invalid email format: {to}")
        
        result = heritage_email.send_test_email(to.strip())
        
        # Create log entry
        email_log = HeritageEmailLog(
            to_emails=to,
            subject="Heritage Trust - Test Email",
            email_type="test"
        )
        
        if result.get('success'):
            email_log.message_id = result.get('message_id')
            email_log.status = "sent"
            logger.info(f"✅ Test email sent: {result.get('message_id')}")
        else:
            email_log.status = "failed"
            email_log.error_message = result.get('error', 'Unknown error')
            logger.error(f"❌ Test failed: {email_log.error_message}")
        
        db.add(email_log)
        db.commit()
        
        if result.get('success'):
            return HeritageEmailResponse(
                success=True,
                message="Test email sent",
                message_id=result.get('message_id'),
                from_email=heritage_email.from_email
            )
        else:
            raise HTTPException(status_code=500, detail=email_log.error_message)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Exception: {str(e)}")
        
        # Log error to database
        try:
            error_log = HeritageEmailLog(
                to_emails=to,
                subject="Heritage Trust - Test Email",
                email_type="test",
                status="failed",
                error_message=str(e)
            )
            db.add(error_log)
            db.commit()
        except:
            pass
        
        raise HTTPException(status_code=500, detail=str(e))

@router.post(
    "/invoice", 
    status_code=status.HTTP_200_OK,
    response_model=HeritageEmailResponse
)
async def send_invoice(
    to: str = Form(..., description="Recipient email address"),
    invoice_number: str = Form(..., description="Invoice number"),
    amount: float = Form(..., description="Invoice amount"),
    description: str = Form(..., description="Invoice description"),
    pdf_attachment: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Send invoice email with optional PDF attachment"""
    logger.info(f"=== Heritage Trust Invoice Request ===")
    logger.info(f"To: {to}, Invoice: {invoice_number}")
    
    pdf_path = None
    
    try:
        # Manual validation
        if not to or not to.strip():
            raise HTTPException(status_code=422, detail="Email address is required")
        
        if '@' not in to or '.' not in to:
            raise HTTPException(status_code=422, detail=f"Invalid email format: {to}")
        
        if not invoice_number or not invoice_number.strip():
            raise HTTPException(status_code=422, detail="Invoice number is required")
        
        if amount <= 0:
            raise HTTPException(status_code=422, detail="Amount must be greater than 0")
        
        if not description or not description.strip():
            raise HTTPException(status_code=422, detail="Description is required")
        
        invoice_data = {
            'invoice_number': invoice_number.strip(),
            'amount': f"{amount:.2f}",
            'description': description.strip(),
            'date': datetime.now().strftime("%Y-%m-%d")
        }
        
        # Handle PDF attachment
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
        
        result = heritage_email.send_invoice(
            to_email=to.strip(),
            invoice_data=invoice_data,
            pdf_path=pdf_path
        )
        
        # Create log entry
        email_log = HeritageEmailLog(
            to_emails=to,
            subject=f"Heritage Trust - Invoice #{invoice_number}",
            email_type="invoice",
            invoice_number=invoice_number,
            invoice_amount=amount,
            invoice_description=description,
            attachments_count=1 if pdf_path else 0
        )
        
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except:
                pass
        
        if result.get('success'):
            email_log.message_id = result.get('message_id')
            email_log.status = "sent"
            logger.info(f"✅ Invoice sent: {result.get('message_id')}")
        else:
            email_log.status = "failed"
            email_log.error_message = result.get('error', 'Unknown error')
            logger.error(f"❌ Invoice failed: {email_log.error_message}")
        
        db.add(email_log)
        db.commit()
        
        if result.get('success'):
            return HeritageEmailResponse(
                success=True,
                message="Invoice sent",
                message_id=result.get('message_id'),
                from_email=heritage_email.from_email
            )
        else:
            raise HTTPException(status_code=500, detail=email_log.error_message)
            
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
        
        logger.error(f"❌ Exception: {str(e)}")
        
        # Log error to database
        try:
            error_log = HeritageEmailLog(
                to_emails=to,
                subject=f"Heritage Trust - Invoice #{invoice_number}",
                email_type="invoice",
                invoice_number=invoice_number,
                invoice_amount=amount,
                invoice_description=description,
                status="failed",
                error_message=str(e)
            )
            db.add(error_log)
            db.commit()
        except:
            pass
        
        raise HTTPException(status_code=500, detail=str(e))

@router.get(
    "/ping", 
    status_code=status.HTTP_200_OK,
    response_model=HeritagePingResponse
)
async def ping():
    """Test endpoint to verify service is running"""
    return HeritagePingResponse(
        status="ok",
        message="Heritage Trust email service is running",
        from_email=heritage_email.from_email,
        from_name=heritage_email.from_name
    )

@router.get("/logs", status_code=status.HTTP_200_OK, response_model=HeritageLogsResponse)
async def get_email_logs(
    skip: int = 0, 
    limit: int = 100,
    status: Optional[str] = None,
    email_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get email sending history"""
    query = db.query(HeritageEmailLog)
    
    if status:
        query = query.filter(HeritageEmailLog.status == status)
    if email_type:
        query = query.filter(HeritageEmailLog.email_type == email_type)
    
    total = query.count()
    logs = query.order_by(
        HeritageEmailLog.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return HeritageLogsResponse(
        total=total,
        logs=[
            HeritageLogEntry.model_validate(log) for log in logs
        ]
    )