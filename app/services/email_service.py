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
    
    async def send_invoice_pdf(self, shipment, pdf_path):
        """Send invoice PDF as attachment"""
        try:
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #1e3c72; padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">EukExpress Global Logistics</h1>
                </div>
                <div style="padding: 20px;">
                    <h2 style="color: #1e293b;">Shipment Created Successfully</h2>
                    <p>Dear {shipment.sender_name},</p>
                    <p>Your shipment has been created successfully. Please find attached the invoice for your records.</p>
                    
                    <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #1e3c72; margin: 20px 0;">
                        <p><strong>Tracking Number:</strong> {shipment.tracking_number}</p>
                        <p><strong>Destination:</strong> {shipment.destination_location}</p>
                        <p><strong>Estimated Delivery:</strong> {shipment.estimated_delivery_date}</p>
                    </div>
                    
                    <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">Click here</a></p>
                </div>
                <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                    <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
                </div>
            </div>
            """
            
            return self.send_email(
                to=[shipment.sender_email],
                subject=f"Invoice for Shipment {shipment.tracking_number}",
                html_content=html_content,
                attachments=[{
                    'filename': f"invoice-{shipment.tracking_number}.pdf",
                    'content': pdf_content,
                    'content_type': 'application/pdf'
                }]
            )
        except Exception as e:
            logger.error(f"Error sending invoice PDF: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_customs_notification(self, shipment, action, data=None):
        """Send customs bond notification"""
        action_text = "activated" if action == "activate" else "released"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1e3c72; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">EukExpress Global Logistics</h1>
            </div>
            <div style="padding: 20px;">
                <h2 style="color: #1e293b;">Shipment Update - Customs Bond {action_text}</h2>
                <p>Dear Customer,</p>
                <p>The customs bond for your shipment has been <strong>{action_text}</strong>.</p>
                
                <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #FF6B35; margin: 20px 0;">
                    <p><strong>Tracking Number:</strong> {shipment.tracking_number}</p>
                    <p><strong>Status:</strong> Customs Bond {action_text.capitalize()}</p>
                    {f'<p><strong>Location:</strong> {data.get("location")}</p>' if data and data.get('location') else ''}
                    {f'<p><strong>Reference:</strong> {data.get("reference")}</p>' if data and data.get('reference') else ''}
                    {f'<p><strong>Notes:</strong> {data.get("notes")}</p>' if data and data.get('notes') else ''}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">Click here</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to both
        self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Customs Bond {action_text}",
            html_content=html_content
        )
        
        if shipment.sender_email != shipment.recipient_email:
            self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Customs Bond {action_text}",
                html_content=html_content
            )
    
    async def send_shipment_created_notification(self, shipment):
        """Send notification to recipient about new shipment"""
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1e3c72; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">EukExpress Global Logistics</h1>
            </div>
            <div style="padding: 20px;">
                <h2 style="color: #1e293b;">A Shipment Has Been Created for You</h2>
                <p>Dear {shipment.recipient_name},</p>
                <p>A shipment has been created for you by {shipment.sender_name}.</p>
                
                <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #1e3c72; margin: 20px 0;">
                    <p><strong>Tracking Number:</strong> {shipment.tracking_number}</p>
                    <p><strong>Origin:</strong> {shipment.origin_location}</p>
                    <p><strong>Destination:</strong> {shipment.destination_location}</p>
                    <p><strong>Estimated Delivery:</strong> {shipment.estimated_delivery_date}</p>
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">Click here</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        return self.send_email(
            to=[shipment.recipient_email],
            subject=f"Shipment {shipment.tracking_number} Created for You",
            html_content=html_content
        )
    
    async def send_status_update_notification(self, shipment, old_status, new_status, location=None, notes=None):
        """Send status update notification to both parties"""
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1e3c72; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">EukExpress Global Logistics</h1>
            </div>
            <div style="padding: 20px;">
                <h2 style="color: #1e293b;">Shipment Status Updated</h2>
                <p>Dear Customer,</p>
                <p>The status of your shipment has been updated.</p>
                
                <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #FF6B35; margin: 20px 0;">
                    <p><strong>Tracking Number:</strong> {shipment.tracking_number}</p>
                    <p><strong>Previous Status:</strong> {old_status}</p>
                    <p><strong>New Status:</strong> {new_status}</p>
                    {f'<p><strong>Location:</strong> {location}</p>' if location else ''}
                    {f'<p><strong>Notes:</strong> {notes}</p>' if notes else ''}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">Click here</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to sender
        self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Status Update",
            html_content=html_content
        )
        
        # Send to recipient if different
        if shipment.sender_email != shipment.recipient_email:
            self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Status Update",
                html_content=html_content
            )
    
    async def send_damage_notification(self, shipment, action, description=None, resolution=None):
        """Send damage notification"""
        action_text = "reported" if action == "report" else "resolved"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1e3c72; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">EukExpress Global Logistics</h1>
            </div>
            <div style="padding: 20px;">
                <h2 style="color: #1e293b;">Shipment Update - Damage {action_text}</h2>
                <p>Dear Customer,</p>
                <p>Damage has been <strong>{action_text}</strong> on your shipment.</p>
                
                <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #FF6B35; margin: 20px 0;">
                    <p><strong>Tracking Number:</strong> {shipment.tracking_number}</p>
                    {f'<p><strong>Description:</strong> {description}</p>' if description else ''}
                    {f'<p><strong>Resolution:</strong> {resolution}</p>' if resolution else ''}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">Click here</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to both
        self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Damage {action_text}",
            html_content=html_content
        )
        
        if shipment.sender_email != shipment.recipient_email:
            self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Damage {action_text}",
                html_content=html_content
            )
    
    async def send_delay_notification(self, shipment, action, reason=None, revised_eta=None):
        """Send delay notification"""
        action_text = "reported" if action == "report" else "resolved"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1e3c72; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">EukExpress Global Logistics</h1>
            </div>
            <div style="padding: 20px;">
                <h2 style="color: #1e293b;">Shipment Update - Delay {action_text}</h2>
                <p>Dear Customer,</p>
                <p>A delay has been <strong>{action_text}</strong> on your shipment.</p>
                
                <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #FF6B35; margin: 20px 0;">
                    <p><strong>Tracking Number:</strong> {shipment.tracking_number}</p>
                    {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
                    {f'<p><strong>Revised ETA:</strong> {revised_eta}</p>' if revised_eta else ''}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">Click here</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to both
        self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Delay {action_text}",
            html_content=html_content
        )
        
        if shipment.sender_email != shipment.recipient_email:
            self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Delay {action_text}",
                html_content=html_content
            )
    
    async def send_security_notification(self, shipment, action, location=None, notes=None):
        """Send security hold notification"""
        action_text = "activated" if action == "activate" else "cleared"
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1e3c72; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">EukExpress Global Logistics</h1>
            </div>
            <div style="padding: 20px;">
                <h2 style="color: #1e293b;">Shipment Update - Security Hold {action_text}</h2>
                <p>Dear Customer,</p>
                <p>A security hold has been <strong>{action_text}</strong> on your shipment.</p>
                
                <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #FF6B35; margin: 20px 0;">
                    <p><strong>Tracking Number:</strong> {shipment.tracking_number}</p>
                    {f'<p><strong>Location:</strong> {location}</p>' if location else ''}
                    {f'<p><strong>Notes:</strong> {notes}</p>' if notes else ''}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">Click here</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to both
        self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Security Hold {action_text}",
            html_content=html_content
        )
        
        if shipment.sender_email != shipment.recipient_email:
            self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Security Hold {action_text}",
                html_content=html_content
            )
    
    async def send_return_notification(self, shipment, reason=None):
        """Send return notification"""
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1e3c72; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">EukExpress Global Logistics</h1>
            </div>
            <div style="padding: 20px;">
                <h2 style="color: #1e293b;">Shipment Update - Return Initiated</h2>
                <p>Dear Customer,</p>
                <p>A return to sender has been initiated for your shipment.</p>
                
                <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #FF6B35; margin: 20px 0;">
                    <p><strong>Tracking Number:</strong> {shipment.tracking_number}</p>
                    {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}">Click here</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to both
        self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Return Initiated",
            html_content=html_content
        )
        
        if shipment.sender_email != shipment.recipient_email:
            self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Return Initiated",
                html_content=html_content
            )
    
    async def send_custom_message(self, tracking_number, recipient_email, recipient_name, subject, message, include_tracking_link=True):
        """Send custom message to specific recipient"""
        tracking_link = f"https://eukexpress.com/track?number={tracking_number}" if include_tracking_link else None
        
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background-color: #1e3c72; padding: 20px; text-align: center;">
                <h1 style="color: white; margin: 0;">EukExpress Global Logistics</h1>
            </div>
            <div style="padding: 20px;">
                <h2 style="color: #1e293b;">Message Regarding Your Shipment</h2>
                <p>Dear {recipient_name},</p>
                <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #FF6B35; margin: 20px 0;">
                    {message}
                </div>
                {f'<p>Track your shipment: <a href="{tracking_link}">Click here</a></p>' if tracking_link else ''}
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        return self.send_email(
            to=[recipient_email],
            subject=subject,
            html_content=html_content
        )

# Global instance
email_service = EmailService()