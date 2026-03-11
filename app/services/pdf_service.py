# EukExpress\backend\app\services\pdf_service.py
"""
PDF Generation Service
Generates professional invoice PDFs
"""

import os
from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
import logging

from app.config import settings

# Configure Jinja2 template environment
template_env = Environment(
    loader=FileSystemLoader("app/templates/pdf"),
    autoescape=True
)

logger = logging.getLogger(__name__)

async def generate_invoice_pdf(shipment):
    """Generate invoice PDF for shipment"""
    try:
        # Create invoices directory if it doesn't exist
        invoice_dir = os.path.join(settings.UPLOAD_PATH, "invoices")
        os.makedirs(invoice_dir, exist_ok=True)
        
        # Render template
        template = template_env.get_template("invoice_template.html")
        
        # Prepare data for template
        dimensions_display = "N/A"
        if shipment.dimensions:
            dimensions_display = f"{shipment.dimensions.get('length', '')}x{shipment.dimensions.get('width', '')}x{shipment.dimensions.get('height', '')} cm"
        
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
            "qr_code_path": os.path.join(settings.QR_CODE_PATH, f"{shipment.tracking_number}.png")
        }
        
        html_content = template.render(**data)
        
        # Generate PDF
        pdf_filename = f"invoice-{shipment.tracking_number}.pdf"
        pdf_path = os.path.join(invoice_dir, pdf_filename)
        
        # Load CSS if exists
        css_path = os.path.join("app/templates/pdf", "styles.css")
        css = CSS(filename=css_path) if os.path.exists(css_path) else None
        
        # Generate PDF
        HTML(string=html_content, base_url=settings.APP_URL).write_pdf(pdf_path)
        
        # Update shipment with PDF path
        shipment.invoice_pdf_path = pdf_path
        
        logger.info(f"Invoice PDF generated for {shipment.tracking_number}")
        return {"success": True, "path": pdf_path}
        
    except Exception as e:
        logger.error(f"Failed to generate PDF for {shipment.tracking_number}: {e}")
        return {"success": False, "error": str(e)}
