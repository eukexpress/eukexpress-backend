"""
Heritage Trust Email Service
Using mandatory onboarding format: onboarding@support.heritagetrust.eukexpress.com
"""

import resend
import base64
import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

class HeritageEmailService:
    """Email service for Heritage Trust - uses onboarding@ format as required by Resend"""
    
    def __init__(self):
        # Use the exact format from settings
        self.api_key = getattr(settings, 'HERITAGE_RESEND_API_KEY', settings.RESEND_API_KEY)
        self.from_email = getattr(settings, 'HERITAGE_FROM_EMAIL', "onboarding@support.heritagetrust.eukexpress.com")
        self.from_name = getattr(settings, 'HERITAGE_FROM_NAME', "Heritage Trust")
        
        # Initialize Resend
        if self.api_key:
            resend.api_key = self.api_key
            logger.info(f"✅ Heritage Email Service initialized")
            logger.info(f"   From: {self.from_name} <{self.from_email}>")
            
            # Test the API key by trying to get the domain info
            try:
                # Optional: Verify the domain is properly set up
                # domains = resend.Domains.list()
                # logger.info(f"   Domains found: {len(domains)}")
                pass
            except Exception as e:
                logger.warning(f"   Could not verify domains: {e}")
        else:
            logger.error("❌ No API key found for Heritage Email Service")
    
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
        Send email with optional attachments using onboarding@ format
        """
        # Format from address with name
        from_formatted = f"{self.from_name} <{self.from_email}>"
        
        # Prepare email parameters
        params = {
            "from": from_formatted,
            "to": to,
            "subject": subject,
        }
        
        # Add content (Resend requires at least one of html or text)
        if html_content and html_content.strip():
            params["html"] = html_content
        if text_content and text_content.strip():
            params["text"] = text_content
            
        # If no content provided, add a default
        if "html" not in params and "text" not in params:
            params["text"] = " "
            
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
                    try:
                        with open(attachment['path'], 'rb') as f:
                            content = f.read()
                        encoded = base64.b64encode(content).decode('utf-8')
                        params["attachments"].append({
                            "filename": attachment.get('filename', Path(attachment['path']).name),
                            "content": encoded
                        })
                        logger.info(f"   Attachment added: {attachment.get('filename')}")
                    except Exception as e:
                        logger.error(f"   Failed to process attachment: {e}")
        
        try:
            # Log the request (without sensitive data)
            logger.info(f"Sending email to {to} from {self.from_email}")
            logger.info(f"   Subject: {subject}")
            logger.info(f"   Attachments: {len(params.get('attachments', []))}")
            
            # Send email
            email = resend.Emails.send(params)
            logger.info(f"✅ Email sent successfully: {email['id']}")
            return {"success": True, "message_id": email['id'], "data": email}
        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_test_email(self, to_email: str) -> Dict[str, Any]:
        """Send a test email to verify configuration"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #003366; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9f9f9; }}
                .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Heritage Trust</h1>
                    <p style="font-size: 14px; opacity: 0.9;">{self.from_email}</p>
                </div>
                <div class="content">
                    <h2>Test Email</h2>
                    <p>This is a test email from <strong>Heritage Trust</strong>.</p>
                    <p>Your email service is configured correctly and ready to send!</p>
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
            text_content="This is a test email from Heritage Trust. Your email service is configured correctly."
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
                    <p style="font-size: 14px;">{self.from_email}</p>
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