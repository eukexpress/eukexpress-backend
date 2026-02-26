"""
Heritage Trust Email Service
Simple email sending service
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
    """Simple email service for Heritage Trust"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'HERITAGE_RESEND_API_KEY', settings.RESEND_API_KEY)
        self.from_email = getattr(settings, 'HERITAGE_FROM_EMAIL', "onboarding@support.heritagetrust.eukexpress.com")
        self.from_name = getattr(settings, 'HERITAGE_FROM_NAME', "Heritage Trust")
        
        if self.api_key:
            resend.api_key = self.api_key
            logger.info(f"✅ Email Service Ready - From: {self.from_name} <{self.from_email}>")
        else:
            logger.error("❌ No API key found")
    
    def send_email(self, 
                   to: List[str], 
                   subject: str, 
                   html_content: Optional[str] = None,
                   text_content: Optional[str] = None,
                   attachments: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Send a simple email
        """
        params = {
            "from": f"{self.from_name} <{self.from_email}>",
            "to": to,
            "subject": subject,
        }
        
        # Add content
        if html_content:
            params["html"] = html_content
        if text_content:
            params["text"] = text_content
        
        # Add attachments if any
        if attachments:
            params["attachments"] = []
            for attachment in attachments:
                if os.path.exists(attachment['path']):
                    with open(attachment['path'], 'rb') as f:
                        content = f.read()
                    params["attachments"].append({
                        "filename": attachment['filename'],
                        "content": base64.b64encode(content).decode('utf-8')
                    })
        
        try:
            email = resend.Emails.send(params)
            logger.info(f"✅ Email sent: {email['id']}")
            return {"success": True, "message_id": email['id']}
        except Exception as e:
            logger.error(f"❌ Failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_test_email(self, to_email: str) -> Dict[str, Any]:
        """Send a test email"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: #003366; color: white; padding: 20px; text-align: center; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Heritage Trust</h1>
                </div>
                <div style="padding: 20px;">
                    <h2>Test Email</h2>
                    <p>This is a test email from Heritage Trust.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self.send_email(
            to=[to_email],
            subject="Heritage Trust - Test Email",
            html_content=html,
            text_content="This is a test email from Heritage Trust."
        )

# Global instance
heritage_email = HeritageEmailService()