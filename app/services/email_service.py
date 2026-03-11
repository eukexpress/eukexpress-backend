"""
EukExpress Email Service
Handles all email sending operations using Resend - COMPLETE FIXED VERSION WITH PDF FOR BOTH
"""
import logging
import resend
import os
import base64
from typing import List, Optional, Dict, Any
import asyncio
from app.config import settings
from app.utils.pdf_utils import get_qr_code_path

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for EukExpress using Resend with verified domain onboarding@delivery.eukexpress.com"""
    
    def __init__(self):
        # Use EUKEXPRESS_* variables for consistency - YOUR PROVEN PATTERN
        self.api_key = settings.EUKEXPRESS_RESEND_API_KEY or settings.RESEND_API_KEY
        self.from_email = settings.EUKEXPRESS_FROM_EMAIL or settings.RESEND_FROM_EMAIL
        self.from_name = settings.EUKEXPRESS_FROM_NAME or settings.RESEND_FROM_NAME
        
        # Configure Resend
        if self.api_key:
            resend.api_key = self.api_key
            logger.info(f"✅ Email service initialized with from_email: {self.from_email}")
            logger.info(f"✅ Email service initialized with from_name: {self.from_name}")
        else:
            logger.error("❌ No Resend API key found - email sending will fail")
    
    def _format_from_address(self) -> str:
        """
        Format from address using YOUR proven pattern that works:
        "Name <email@domain.com>"
        """
        if not self.from_email:
            logger.error("❌ from_email is empty - cannot format address")
            return ""
        
        if not self.from_name:
            logger.warning("⚠️ from_name is empty, using email only")
            return self.from_email
        
        # YOUR PROVEN PATTERN - This is what you've used for months successfully
        formatted = f"{self.from_name} <{self.from_email}>"
        logger.info(f"📧 Formatted from address: {formatted}")
        return formatted
    
    async def send_email(
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
                logger.error("❌ Resend API key not configured")
                return {"success": False, "error": "Resend API key not configured"}
            
            # Format from address using YOUR proven pattern
            from_address = self._format_from_address()
            
            if not from_address:
                logger.error("❌ Failed to format from_address")
                return {"success": False, "error": "Invalid from address configuration"}
            
            # Prepare email params
            params = {
                "from": from_address,
                "to": to,
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                params["text"] = text_content
            
            # IMPORTANT FIX: Resend expects attachments with base64 content, not bytes
            if attachments:
                formatted_attachments = []
                for attachment in attachments:
                    # Ensure content is base64 encoded string, not bytes
                    content = attachment.get('content')
                    if isinstance(content, bytes):
                        # Convert bytes to base64 string
                        content = base64.b64encode(content).decode('utf-8')
                    
                    formatted_attachments.append({
                        'filename': attachment.get('filename'),
                        'content': content,
                        'content_type': attachment.get('content_type', 'application/octet-stream')
                    })
                params["attachments"] = formatted_attachments
                logger.info(f"📎 Email has {len(attachments)} attachment(s)")
            
            # Send email
            logger.info(f"📧 Sending email from: {from_address} to: {to}, subject: {subject}")
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: resend.Emails.send(params)
            )
            
            logger.info(f"✅ Email sent successfully: {response['id']}")
            return {"success": True, "id": response["id"]}
            
        except Exception as e:
            logger.error(f"❌ Error sending email: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def send_test_email(self, to_email: str) -> Dict[str, Any]:
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
                <p style="color: #666;"><strong>From:</strong> EukExpress Global Logistics (verified domain)</p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>(c) 2025 EukExpress Global Logistics. All rights reserved.</p>
            </div>
        </div>
        """
        
        return await self.send_email(
            to=[to_email],
            subject="EukExpress - Test Email",
            html_content=html_content
        )
    
    async def send_invoice_pdf(self, shipment, pdf_path, recipient_email=None):
        """
        Send invoice PDF as attachment to sender (and optionally recipient)
        This is used for the SENDER email
        """
        try:
            with open(pdf_path, 'rb') as f:
                pdf_content = f.read()
            
            # Convert bytes to base64 for Resend
            pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            
            # Determine who to send to - always include sender
            to_emails = [shipment.sender_email]
            if recipient_email:
                to_emails.append(recipient_email)
            
            html_content = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background-color: #1e3c72; padding: 20px; text-align: center;">
                    <h1 style="color: white; margin: 0;">EukExpress Global Logistics</h1>
                </div>
                <div style="padding: 20px;">
                    <h2 style="color: #1e293b;">Shipment Created Successfully</h2>
                    <p>Dear {shipment.sender_name},</p>
                    <p>Your shipment has been created with tracking number <strong>{shipment.tracking_number}</strong>.</p>
                    
                    <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #1e3c72; margin: 20px 0;">
                        <p><strong>Tracking Number:</strong> {shipment.tracking_number}</p>
                        <p><strong>Origin:</strong> {shipment.origin_location}</p>
                        <p><strong>Destination:</strong> {shipment.destination_location}</p>
                        <p><strong>Estimated Delivery:</strong> {shipment.estimated_delivery_date}</p>
                    </div>
                    
                    <div style="background-color: #e6f7e6; padding: 15px; border-radius: 8px; margin: 20px 0; border: 2px solid #28a745;">
                        <p style="margin: 0; font-size: 16px; color: #1e3c72;">
                            <strong>📎 ATTACHMENT:</strong> The invoice PDF with QR code is attached to this email.
                        </p>
                    </div>
                    
                    <p>Track your shipment online: <a href="https://eukexpress.com/track?number={shipment.tracking_number}" style="background-color: #1e3c72; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Track Now</a></p>
                </div>
                <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                    <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
                    <p>This email contains an attached PDF invoice. If you cannot see the attachment, please check your email client's download section.</p>
                </div>
            </div>
            """
            
            result = await self.send_email(
                to=to_emails,
                subject=f"📎 Shipment {shipment.tracking_number} - Invoice Attached",
                html_content=html_content,
                attachments=[{
                    'filename': f"invoice-{shipment.tracking_number}.pdf",
                    'content': pdf_base64,
                    'content_type': 'application/pdf'
                }]
            )
            
            if result.get("success"):
                logger.info(f"✅ Invoice PDF sent to sender: {shipment.sender_email}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending invoice PDF: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def send_shipment_created_notification(self, shipment, pdf_path=None):
        """
        Send notification to recipient about new shipment with PDF attached
        This is used for the RECIPIENT email
        """
        try:
            # Prepare PDF attachment if available
            attachments = []
            has_pdf = False
            
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, 'rb') as f:
                    pdf_content = f.read()
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                attachments.append({
                    'filename': f"invoice-{shipment.tracking_number}.pdf",
                    'content': pdf_base64,
                    'content_type': 'application/pdf'
                })
                has_pdf = True
                logger.info(f"✅ PDF attached to recipient email: {pdf_path}")
            else:
                logger.warning(f"⚠️ PDF not found for recipient, sending without attachment")
            
            # Email HTML content - clearly indicates PDF is attached with visible notice
            pdf_notice = ""
            if has_pdf:
                pdf_notice = """
                <div style="background-color: #e6f7e6; padding: 15px; border-radius: 8px; margin: 20px 0; border: 2px solid #28a745;">
                    <p style="margin: 0; font-size: 16px; color: #1e3c72;">
                        <strong>📎 ATTACHMENT:</strong> The invoice PDF with QR code is attached to this email. 
                        Please check your email client for the attached file.
                    </p>
                </div>
                """
            
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
                    
                    {pdf_notice}
                    
                    <p>Track your shipment online: <a href="https://eukexpress.com/track?number={shipment.tracking_number}" style="background-color: #1e3c72; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Track Now</a></p>
                </div>
                <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                    <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
                    <p>This email contains an attached PDF invoice. If you cannot see the attachment, please check your email client's download section.</p>
                </div>
            </div>
            """
            
            # Subject line includes paperclip emoji to indicate attachment
            subject = f"📎 Shipment {shipment.tracking_number} Created for You - Invoice Attached" if has_pdf else f"Shipment {shipment.tracking_number} Created for You"
            
            result = await self.send_email(
                to=[shipment.recipient_email],
                subject=subject,
                html_content=html_content,
                attachments=attachments if attachments else None
            )
            
            if result.get("success"):
                logger.info(f"✅ Email with PDF attachment sent to recipient: {shipment.recipient_email}")
            else:
                logger.error(f"❌ Failed to send email to recipient: {result.get('error')}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error sending shipment notification to recipient: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def send_status_update_notification(self, shipment, old_status, new_status, location=None, notes=None):
        """Send status update notification to both parties"""
        location_html = f"<p><strong>Location:</strong> {location}</p>" if location else ""
        notes_html = f"<p><strong>Notes:</strong> {notes}</p>" if notes else ""
        
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
                    {location_html}
                    {notes_html}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}" style="background-color: #1e3c72; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Track Now</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to sender
        result1 = await self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Status Update",
            html_content=html_content
        )
        
        # Send to recipient if different
        result2 = {"success": True}
        if shipment.sender_email != shipment.recipient_email:
            result2 = await self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Status Update",
                html_content=html_content
            )
        
        return result1["success"] and result2["success"]
    
    async def send_customs_notification(self, shipment, action, data=None):
        """Send customs bond notification"""
        action_text = "activated" if action == "activate" else "released"
        
        # Build location/reference details
        details = ""
        if data:
            if data.get('location'):
                details += f"<p><strong>Location:</strong> {data['location']}</p>"
            if data.get('reference'):
                details += f"<p><strong>Reference:</strong> {data['reference']}</p>"
            if data.get('notes'):
                details += f"<p><strong>Notes:</strong> {data['notes']}</p>"
        
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
                    {details}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}" style="background-color: #1e3c72; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Track Now</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to sender
        result1 = await self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Customs Bond {action_text}",
            html_content=html_content
        )
        
        # Send to recipient if different
        result2 = {"success": True}
        if shipment.sender_email != shipment.recipient_email:
            result2 = await self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Customs Bond {action_text}",
                html_content=html_content
            )
        
        return result1["success"] and result2["success"]
    
    async def send_security_notification(self, shipment, action, location=None, notes=None):
        """Send security hold notification"""
        action_text = "activated" if action == "activate" else "cleared"
        
        details = ""
        if location:
            details += f"<p><strong>Location:</strong> {location}</p>"
        if notes:
            details += f"<p><strong>Notes:</strong> {notes}</p>"
        
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
                    {details}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}" style="background-color: #1e3c72; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Track Now</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to sender
        result1 = await self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Security Hold {action_text}",
            html_content=html_content
        )
        
        # Send to recipient if different
        result2 = {"success": True}
        if shipment.sender_email != shipment.recipient_email:
            result2 = await self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Security Hold {action_text}",
                html_content=html_content
            )
        
        return result1["success"] and result2["success"]
    
    async def send_damage_notification(self, shipment, action, description=None, resolution=None):
        """Send damage notification"""
        action_text = "reported" if action == "report" else "resolved"
        
        details = ""
        if description:
            details += f"<p><strong>Description:</strong> {description}</p>"
        if resolution:
            details += f"<p><strong>Resolution:</strong> {resolution}</p>"
        
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
                    {details}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}" style="background-color: #1e3c72; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Track Now</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to sender
        result1 = await self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Damage {action_text}",
            html_content=html_content
        )
        
        # Send to recipient if different
        result2 = {"success": True}
        if shipment.sender_email != shipment.recipient_email:
            result2 = await self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Damage {action_text}",
                html_content=html_content
            )
        
        return result1["success"] and result2["success"]
    
    async def send_delay_notification(self, shipment, action, reason=None, revised_eta=None):
        """Send delay notification"""
        action_text = "reported" if action == "report" else "resolved"
        
        details = ""
        if reason:
            details += f"<p><strong>Reason:</strong> {reason}</p>"
        if revised_eta:
            details += f"<p><strong>Revised ETA:</strong> {revised_eta}</p>"
        
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
                    {details}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}" style="background-color: #1e3c72; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Track Now</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to sender
        result1 = await self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Delay {action_text}",
            html_content=html_content
        )
        
        # Send to recipient if different
        result2 = {"success": True}
        if shipment.sender_email != shipment.recipient_email:
            result2 = await self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Delay {action_text}",
                html_content=html_content
            )
        
        return result1["success"] and result2["success"]
    
    async def send_return_notification(self, shipment, reason=None):
        """Send return notification"""
        reason_html = f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""
        
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
                    {reason_html}
                </div>
                
                <p>Track your shipment: <a href="https://eukexpress.com/track?number={shipment.tracking_number}" style="background-color: #1e3c72; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Track Now</a></p>
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        # Send to sender
        result1 = await self.send_email(
            to=[shipment.sender_email],
            subject=f"Shipment {shipment.tracking_number} - Return Initiated",
            html_content=html_content
        )
        
        # Send to recipient if different
        result2 = {"success": True}
        if shipment.sender_email != shipment.recipient_email:
            result2 = await self.send_email(
                to=[shipment.recipient_email],
                subject=f"Shipment {shipment.tracking_number} - Return Initiated",
                html_content=html_content
            )
        
        return result1["success"] and result2["success"]
    
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
                {f'<p>Track your shipment: <a href="{tracking_link}" style="background-color: #1e3c72; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Track Now</a></p>' if tracking_link else ''}
            </div>
            <div style="background-color: #f5f5f5; padding: 10px; text-align: center; font-size: 12px; color: #999;">
                <p>EukExpress Global Logistics - Your Trusted Shipping Partner</p>
            </div>
        </div>
        """
        
        return await self.send_email(
            to=[recipient_email],
            subject=subject,
            html_content=html_content
        )

# Global instance
email_service = EmailService()