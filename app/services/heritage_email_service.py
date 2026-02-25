"""
Heritage Trust Email Service
Using Resend API with subdomain heritagetrust.eukexpress.com
Supports text, images, and PDF attachments
"""

import resend
import base64
import os
from typing import List, Optional
from pathlib import Path

# Configure Resend with your API key
RESEND_API_KEY = "re_hSXDoJjW_4U6xwL4AtgvCaucNYmwHaTa2"
resend.api_key = RESEND_API_KEY

class HeritageEmailService:
    """Email service for Heritage Trust using Resend"""
    
    def __init__(self):
        self.from_email = "Heritage Trust <notifications@heritagetrust.eukexpress.com>"
        
    def send_email(self, 
                   to: List[str], 
                   subject: str, 
                   html_content: str = None,
                   text_content: str = None,
                   attachments: List[dict] = None,
                   cc: List[str] = None,
                   bcc: List[str] = None,
                   reply_to: str = None):
        """
        Send email with optional attachments
        
        Args:
            to: List of recipient emails
            subject: Email subject
            html_content: HTML version of email
            text_content: Plain text version (fallback)
            attachments: List of attachment dicts with 'filename', 'content', and 'path'
            cc: Carbon copy recipients
            bcc: Blind carbon copy recipients
            reply_to: Reply-to address
        """
        
        # Prepare email parameters
        params = {
            "from": self.from_email,
            "to": to,
            "subject": subject,
        }
        
        # Add content (prefer HTML, fallback to text)
        if html_content:
            params["html"] = html_content
        elif text_content:
            params["text"] = text_content
        else:
            params["text"] = " "  # Empty fallback
            
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
                # If file path is provided, read and encode it
                if 'path' in attachment:
                    with open(attachment['path'], 'rb') as f:
                        content = f.read()
                    encoded = base64.b64encode(content).decode('utf-8')
                    params["attachments"].append({
                        "filename": attachment.get('filename', Path(attachment['path']).name),
                        "content": encoded
                    })
                # If content is provided directly
                elif 'content' in attachment:
                    # Ensure content is base64 encoded
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
            email = resend.Emails.send(params)
            print(f"✅ Email sent successfully: {email['id']}")
            return {"success": True, "message_id": email['id'], "data": email}
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_test_email(self, to_email: str):
        """Send a test email"""
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
                    <p>This is a test email from Heritage Trust using <strong>heritagetrust.eukexpress.com</strong>.</p>
                    <p>Your email service is configured correctly!</p>
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
            text_content="This is a test email from Heritage Trust. Your email service is configured correctly!"
        )
    
    def send_invoice(self, to_email: str, invoice_data: dict, pdf_path: str = None):
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