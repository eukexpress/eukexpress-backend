# Eukexpress\backend\app\services\email_service.py
"""
EukExpress Email Service
Handles all email sending operations using Resend
"""
import logging
import resend
from typing import List, Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for EukExpress using Resend with verified domain onboarding@delivery.eukexpress.com"""
    
    def __init__(self):
        # Use EUKEXPRESS_* variables for consistency
        self.api_key = settings.EUKEXPRESS_RESEND_API_KEY or settings.RESEND_API_KEY
        self.from_email = settings.EUKEXPRESS_FROM_EMAIL or settings.RESEND_FROM_EMAIL
        self.from_name = settings.EUKEXPRESS_FROM_NAME or settings.RESEND_FROM_NAME
        
        # Configure Resend
        if self.api_key:
            resend.api_key = self.api_key
            logger.info(f"✅ Email service initialized with from: {self.from_name} <{self.from_email}>")
        else:
            logger.error("❌ No Resend API key found - email sending will fail")
    
    def send_email(
        self,
        to: List[str],
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Send an email using Resend"""
        try:
            if not self.api_key:
                return {"success": False, "error": "Resend API key not configured"}
            
            # Prepare email params
            params = {
                "from": f"{self.from_name} <{self.from_email}>",
                "to": to,
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                params["text"] = text_content
            
            if attachments:
                params["attachments"] = attachments
            
            # Send email
            logger.info(f"📧 Sending email to: {to}, subject: {subject}")
            response = resend.Emails.send(params)
            
            logger.info(f"✅ Email sent successfully: {response['id']}")
            return {"success": True, "id": response["id"]}
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {e}")
            return {"success": False, "error": str(e)}
    
    def send_test_email(self, to: str) -> Dict[str, Any]:
        """Send a test email"""
        html_content = """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #0047ab; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">EukExpress Global Logistics</h1>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd;">
                <h2 style="color: #333;">Test Email</h2>
                <p style="color: #666;">This is a test email from EukExpress Global Logistics.</p>
                <p style="color: #666;">If you received this, the email service is working correctly.</p>
                <p style="color: #666;"><strong>From:</strong> onboarding@delivery.eukexpress.com (verified domain)</p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>(c) 2025 EukExpress Global Logistics. All rights reserved.</p>
            </div>
        </div>
        """
        
        text_content = "EukExpress Global Logistics - Test Email\n\nThis is a test email from EukExpress. If you received this, the email service is working correctly."
        
        return self.send_email(
            to=[to],
            subject="EukExpress - Test Email",
            html_content=html_content,
            text_content=text_content
        )

# Global instance
email_service = EmailService()