"""
Heritage Trust Email Service
Using dedicated environment variables to avoid conflicts
"""

import resend
import base64
import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.config import settings

# Configure logger
logger = logging.getLogger(__name__)

class HeritageEmailService:
    """Email service for Heritage Trust using dedicated env vars"""
    
    def __init__(self):
        # Use HERITAGE-specific variables from settings
        # Note: You'll need to add these to your config.py
        self.api_key = os.environ.get("HERITAGE_RESEND_API_KEY", "")
        self.from_email = os.environ.get("HERITAGE_FROM_EMAIL", "support@heritagetrust.eukexpress.com")
        self.from_name = os.environ.get("HERITAGE_FROM_NAME", "Heritage Trust")
        
        # Initialize Resend with the Heritage-specific key
        if self.api_key:
            resend.api_key = self.api_key
            logger.info(f"✅ Heritage Email Service initialized with from: {self.from_email}")
        else:
            logger.error("❌ HERITAGE_RESEND_API_KEY not found in environment")
        
    def send_email(self, 
                   to: List[str], 
                   subject: str, 
                   html_content: Optional[str] = None,
                   text_content: Optional[str] = None,
                   attachments: Optional[List[Dict]] = None,
                   cc: Optional[List[str]] = None,
                   bcc: Optional[List[str]] = None,
                   reply_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Send email with optional attachments
        """
        # Format from address with name
        from_formatted = f"{self.from_name} <{self.from_email}>"
        
        # Prepare email parameters
        params: resend.Emails.SendParams = {
            "from": from_formatted,
            "to": to,
            "subject": subject,
        }
        
        # Add content (prefer HTML, fallback to text)
        if html_content:
            params["html"] = html_content
        if text_content:
            params["text"] = text_content
            
        # Optional fields
        if cc:
            params["cc"] = cc
        if bcc:
            params["bcc"] = bcc
        if reply_to:
            params["reply_to"] = reply_to
            
        # Handle attachments
        if attachments:
            params["attachments"] = []
            for attachment in attachments:
                if 'path' in attachment and os.path.exists(attachment['path']):
                    with open(attachment['path'], 'rb') as f:
                        content = f.read()
                    encoded = base64.b64encode(content).decode('utf-8')
                    params["attachments"].append({
                        "filename": attachment.get('filename', Path(attachment['path']).name),
                        "content": encoded
                    })
                elif 'content' in attachment:
                    if isinstance(attachment['content'], bytes):
                        encoded = base64.b64encode(attachment['content']).decode('utf-8')
                    else:
                        encoded = attachment['content']
                    params["attachments"].append({
                        "filename": attachment['filename'],
                        "content": encoded
                    })
        
        try:
            # Send email
            logger.info(f"Sending Heritage Trust email to {to} with subject: {subject}")
            email = resend.Emails.send(params)
            logger.info(f"✅ Heritage Trust email sent successfully: {email['id']}")
            return {"success": True, "message_id": email['id'], "data": email}
        except Exception as e:
            logger.error(f"❌ Failed to send Heritage Trust email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_test_email(self, to_email: str) -> Dict[str, Any]:
        """Send a test email to verify configuration"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #003366; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; background: #f9f9f9; }
                .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Heritage Trust</h1>
                </div>
                <div class="content">
                    <h2>Test Email</h2>
                    <p>This is a test email from Heritage Trust using <strong>support@heritagetrust.eukexpress.com</strong>.</p>
                    <p>Your dedicated email service is configured correctly!</p>
                </div>
                <div class="footer">
                    <p>Heritage Trust - Powered by EukExpress</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to=[to_email],
            subject="Heritage Trust - Test Email",
            html_content=html_content,
            text_content="This is a test email from Heritage Trust. Your dedicated email service is configured correctly!"
        )
    
    def send_invoice(self, to_email: str, invoice_data: dict, pdf_path: Optional[str] = None) -> Dict[str, Any]:
        """Send invoice email with optional PDF attachment"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .invoice {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; }}
                .header {{ background: #003366; color: white; padding: 20px; text-align: center; }}
                .details {{ margin: 20px 0; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="invoice">
                <div class="header">
                    <h1>Heritage Trust</h1>
                    <p>Invoice #{invoice_data.get('invoice_number', 'N/A')}</p>
                </div>
                <div class="details">
                    <p><strong>Date:</strong> {invoice_data.get('date', 'N/A')}</p>
                    <p><strong>Amount:</strong> ${invoice_data.get('amount', '0.00')}</p>
                    <p><strong>Description:</strong> {invoice_data.get('description', 'N/A')}</p>
                </div>
                <div class="footer">
                    <p>Thank you for your business!</p>
                    <p>Heritage Trust - Powered by EukExpress</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        attachments = []
        if pdf_path and os.path.exists(pdf_path):
            attachments.append({
                'path': pdf_path,
                'filename': f"invoice_{invoice_data.get('invoice_number', 'N/A')}.pdf"
            })
        
        return self.send_email(
            to=[to_email],
            subject=f"Heritage Trust - Invoice #{invoice_data.get('invoice_number', 'N/A')}",
            html_content=html_content,
            text_content=f"Your invoice #{invoice_data.get('invoice_number', 'N/A')} is attached.",
            attachments=attachments
        )

# Global instance
heritage_email = HeritageEmailService()