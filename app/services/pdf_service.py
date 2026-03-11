"""
PDF Generation Service
Generates professional invoice PDFs - COMPLETE FIXED VERSION
"""

import os
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import logging

from app.config import settings
from app.utils.pdf_utils import (
    ensure_directory_exists,
    get_qr_code_path,
    format_qr_code_url,
    html_to_pdf,
    format_dimensions,
    get_pdf_path
)

# Configure Jinja2 template environment
template_env = Environment(
    loader=FileSystemLoader("app/templates/pdf"),
    autoescape=True
)

logger = logging.getLogger(__name__)

async def generate_invoice_pdf(shipment):
    """
    Generate invoice PDF for shipment
    
    Args:
        shipment: Shipment database object
    
    Returns:
        Dictionary with success status and path or error
    """
    try:
        # Ensure invoices directory exists
        invoice_dir = os.path.join(settings.UPLOAD_PATH, "invoices")
        ensure_directory_exists(invoice_dir)
        
        # Render template
        template = template_env.get_template("invoice_template.html")
        
        # Get QR code path and format as file:// URL
        qr_code_path = get_qr_code_path(settings.QR_CODE_PATH, shipment.tracking_number)
        qr_code_url = format_qr_code_url(qr_code_path)
        
        # Format dimensions
        dimensions_display = format_dimensions(shipment.dimensions)
        
        # Prepare data for template
        data = {
            "tracking": shipment.tracking_number,
            "invoice_number": shipment.invoice_number,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "sender": {
                "name": shipment.sender_name,
                "email": shipment.sender_email,
                "phone": shipment.sender_phone,
                "address": shipment.sender_address
            },
            "recipient": {
                "name": shipment.recipient_name,
                "email": shipment.recipient_email,
                "phone": shipment.recipient_phone,
                "address": shipment.recipient_address
            },
            "origin": shipment.origin_location,
            "destination": shipment.destination_location,
            "goods": shipment.goods_description,
            "weight": float(shipment.weight_kg) if shipment.weight_kg else "N/A",
            "dimensions": dimensions_display,
            "declared_value": float(shipment.declared_value) if shipment.declared_value else 0,
            "declared_currency": shipment.declared_currency,
            "shipping_amount": float(shipment.shipping_amount),
            "payment_method": shipment.payment_method or "N/A",
            "payment_status": shipment.payment_status,
            "sending_date": shipment.sending_date.strftime("%Y-%m-%d") if shipment.sending_date else "N/A",
            "estimated_delivery": shipment.estimated_delivery_date.strftime("%Y-%m-%d") if shipment.estimated_delivery_date else "N/A",
            "qr_code_path": qr_code_url
        }
        
        # Render HTML
        html_content = template.render(**data)
        
        # Get PDF path
        pdf_path = get_pdf_path(invoice_dir, shipment.tracking_number)
        
        # Generate PDF - USING FIXED FUNCTION
        success = html_to_pdf(html_content, pdf_path, settings.APP_URL)
        
        if not success:
            raise Exception("PDF generation failed")
        
        # Update shipment with PDF path
        shipment.invoice_pdf_path = pdf_path
        
        logger.info(f"✅ Invoice PDF generated for {shipment.tracking_number}")
        return {"success": True, "path": pdf_path}
        
    except Exception as e:
        logger.error(f"❌ Failed to generate PDF for {shipment.tracking_number}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}