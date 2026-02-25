"""
Heritage Trust Email API Endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional, List
import os
import tempfile
from datetime import datetime

from app.services.heritage_email_service import heritage_email

router = APIRouter(prefix="/api/v1/heritage", tags=["Heritage Trust Email"])

@router.post("/send")
async def send_email(
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
    
    # Parse recipients
    recipients = [email.strip() for email in to.split(',')]
    
    # Prepare attachments
    attachment_list = []
    temp_files = []  # Track temp files for cleanup
    
    if attachments:
        for file in attachments:
            if file.filename:
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
            except:
                pass
        
        if result['success']:
            return {
                "success": True,
                "message": "Email sent successfully",
                "message_id": result['message_id']
            }
        else:
            raise HTTPException(status_code=500, detail=result['error'])
            
    except Exception as e:
        # Clean up temp files on error
        for temp_file in temp_files:
            try:
                os.unlink(temp_file)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def send_test_email(to: str = Form(...)):
    """Send a test email to verify configuration"""
    result = heritage_email.send_test_email(to)
    if result['success']:
        return {"success": True, "message": "Test email sent", "message_id": result['message_id']}
    else:
        raise HTTPException(status_code=500, detail=result['error'])

@router.post("/invoice")
async def send_invoice(
    to: str = Form(...),
    invoice_number: str = Form(...),
    amount: float = Form(...),
    description: str = Form(...),
    pdf_attachment: Optional[UploadFile] = File(None)
):
    """Send invoice email with optional PDF"""
    
    invoice_data = {
        'invoice_number': invoice_number,
        'amount': f"{amount:.2f}",
        'description': description,
        'date': datetime.now().strftime("%Y-%m-%d")
    }
    
    # Handle PDF attachment
    pdf_path = None
    if pdf_attachment and pdf_attachment.filename:
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
        
        if result['success']:
            return {"success": True, "message": "Invoice sent", "message_id": result['message_id']}
        else:
            raise HTTPException(status_code=500, detail=result['error'])
            
    except Exception as e:
        if pdf_path:
            try:
                os.unlink(pdf_path)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))