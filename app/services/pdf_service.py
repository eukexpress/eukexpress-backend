"""
PDF Generation Service
Generates professional invoice PDFs using ReportLab - NO EXTERNAL DEPENDENCIES!
"""

import os
from datetime import datetime
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
from io import BytesIO

from app.config import settings

logger = logging.getLogger(__name__)

def format_date_for_pdf(date_value):
    """
    Helper function to format date for PDF display
    Handles both datetime objects and string dates
    """
    if not date_value:
        return "N/A"
    
    # If it's already a datetime/date object with strftime method
    if hasattr(date_value, 'strftime'):
        try:
            return date_value.strftime('%d %b, %Y')
        except:
            pass
    
    # If it's a string, try to parse it
    if isinstance(date_value, str):
        try:
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                try:
                    date_obj = datetime.strptime(date_value, fmt)
                    return date_obj.strftime('%d %b, %Y')
                except:
                    continue
        except:
            pass
    
    # Fallback: return as string
    return str(date_value)

async def generate_invoice_pdf(shipment):
    """
    Generate invoice PDF for shipment using ReportLab
    
    Args:
        shipment: Shipment database object
    
    Returns:
        Dictionary with success status and path or error
    """
    try:
        # Create invoices directory if it doesn't exist
        invoice_dir = os.path.join(settings.UPLOAD_PATH, "invoices")
        os.makedirs(invoice_dir, exist_ok=True)
        
        # PDF filename
        pdf_filename = f"invoice-{shipment.tracking_number}.pdf"
        pdf_path = os.path.join(invoice_dir, pdf_filename)
        
        # Create the PDF document with adjusted margins to fit everything on one page
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=50,  # Reduced top margin
            bottomMargin=50,  # Reduced bottom margin
        )
        
        # Container for the 'Flowable' objects
        story = []
        
        # Get base styles
        styles = getSampleStyleSheet()
        
        # Define custom style names that don't conflict with existing ones
        custom_styles = {
            'CustomRightAlign': ParagraphStyle(
                name='CustomRightAlign',
                parent=styles['Normal'],
                alignment=TA_RIGHT,
                fontSize=9,  # Slightly smaller font
            ),
            'CustomCenterAlign': ParagraphStyle(
                name='CustomCenterAlign',
                parent=styles['Normal'],
                alignment=TA_CENTER,
                fontSize=10,
            ),
            'CustomTitle': ParagraphStyle(
                name='CustomTitle',
                parent=styles['Heading1'],
                alignment=TA_LEFT,  # Changed to left align to make room for QR
                textColor=colors.HexColor('#003366'),
                fontSize=20,  # Slightly smaller title
                spaceAfter=10,
                fontName='Helvetica-Bold',
            ),
            'CustomNormal': ParagraphStyle(
                name='CustomNormal',
                parent=styles['Normal'],
                fontSize=9,  # Slightly smaller font
                leading=12,  # Tighter line spacing
            ),
            'CustomBold': ParagraphStyle(
                name='CustomBold',
                parent=styles['Normal'],
                fontSize=9,  # Slightly smaller font
                fontName='Helvetica-Bold',
                leading=12,  # Tighter line spacing
            ),
        }
        
        # Add custom styles
        for style in custom_styles.values():
            styles.add(style)
        
        # ============================================
        # HEADER with QR CODE (TOP RIGHT)
        # ============================================
        
        # Generate QR code (top right)
        qr_reportlab = None
        try:
            # Generate QR code pointing to frontend tracking page
            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://eukexpress.com')
            qr_data = f"{frontend_url}/track.html?number={shipment.tracking_number}"
            
            # Create QR code image
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=8,  # Slightly smaller box size
                border=2,  # Smaller border
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert PIL image to bytes for ReportLab
            img_buffer = BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Create ReportLab Image (smaller size)
            qr_reportlab = Image(img_buffer, width=1.2*inch, height=1.2*inch)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not generate QR code: {e}")
        
        # Create header with company name on left and QR on right
        header_data = []
        
        if qr_reportlab:
            # Two-column layout: Company name (left) and QR code (right)
            company_name = Paragraph("<b>EukExpress Global Logistics</b>", styles['CustomTitle'])
            header_data = [[company_name, qr_reportlab]]
            header_colwidths = [350, 100]  # Allocate space for QR code
        else:
            # Just company name if QR code failed
            company_name = Paragraph("<b>EukExpress Global Logistics</b>", styles['CustomTitle'])
            header_data = [[company_name]]
            header_colwidths = [450]
        
        header_table = Table(header_data, colWidths=header_colwidths)
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (-1, 0), (-1, 0), 'RIGHT') if qr_reportlab else ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))  # Reduced spacing
        
        # ============================================
        # CONTACT INFORMATION
        # ============================================
        contact_data = [
            [Paragraph("Contact US", styles['CustomRightAlign'])],
            [Paragraph(f"Address: {shipment.sender_address}", styles['CustomRightAlign'])],
            [Paragraph("Email: delivery@eukexpress.com", styles['CustomRightAlign'])],  # CHANGED HERE
        ]
        contact_table = Table(contact_data, colWidths=[450])
        contact_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ]))
        story.append(contact_table)
        story.append(Spacer(1, 10))
        
        # ============================================
        # TRACKING SECTION - FIXED DATE HANDLING
        # ============================================
        sending_date_formatted = format_date_for_pdf(shipment.sending_date)
        
        tracking_data = [
            [Paragraph(f"<b>Tracking ID: {shipment.tracking_number}</b>", styles['CustomBold'])],
            [Paragraph(f"Date of shipment: {sending_date_formatted}", styles['CustomNormal'])],
        ]
        tracking_table = Table(tracking_data, colWidths=[450])
        tracking_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f5f5f5')),
            ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#f5f5f5')),
            ('LEFTPADDING', (0, 0), (0, -1), 20),
            ('BOTTOMPADDING', (0, 0), (0, 0), 8),
            ('TOPPADDING', (0, 1), (0, 1), 8),
        ]))
        story.append(tracking_table)
        story.append(Spacer(1, 10))
        
        # ============================================
        # SENDER AND RECEIVER GRID
        # ============================================
        sender_text = f"""
        <b>SENDER</b><br/><br/>
        {shipment.sender_name}<br/>
        {shipment.sender_address}<br/>
        {shipment.sender_email}<br/>
        {shipment.sender_phone}
        """
        
        receiver_text = f"""
        <b>RECEIVER</b><br/><br/>
        {shipment.recipient_name}<br/>
        {shipment.recipient_address}<br/>
        {shipment.recipient_email}<br/>
        {shipment.recipient_phone}
        """
        
        parties_data = [
            [Paragraph(sender_text, styles['CustomNormal']), 
             Paragraph(receiver_text, styles['CustomNormal'])]
        ]
        
        parties_table = Table(parties_data, colWidths=[225, 225])
        parties_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),  # Reduced padding
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),  # Reduced padding
            ('TOPPADDING', (0, 0), (-1, -1), 10),  # Reduced padding
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),  # Reduced padding
        ]))
        story.append(parties_table)
        story.append(Spacer(1, 10))
        
        # ============================================
        # DESTINATION AND COMMENTS (SAME ROW)
        # ============================================
        dest_text = f"<b>Destination: {shipment.destination_location}</b>"
        comment_text = f"<b>Comments: {shipment.declared_currency} {shipment.declared_value or 0}</b>"
        
        # Put destination and comments in a 2-column table
        dest_comment_data = [
            [Paragraph(dest_text, styles['CustomBold']), 
             Paragraph(comment_text, styles['CustomBold'])]
        ]
        dest_comment_table = Table(dest_comment_data, colWidths=[225, 225])
        dest_comment_table.setStyle(TableStyle([
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#fff3cd')),
            ('BOX', (1, 0), (1, 0), 1, colors.HexColor('#ffeeba')),
            ('LEFTPADDING', (0, 0), (0, 0), 5),
            ('LEFTPADDING', (1, 0), (1, 0), 10),
            ('TOPPADDING', (0, 0), (1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (1, 0), 8),
        ]))
        story.append(dest_comment_table)
        story.append(Spacer(1, 10))
        
        # ============================================
        # PARCEL DESCRIPTION
        # ============================================
        story.append(Paragraph("<b>PARCEL DESCRIPTION</b>", styles['CustomBold']))
        story.append(Spacer(1, 5))
        
        # Format dimensions
        dimensions_display = "N/A"
        if hasattr(shipment, 'dimensions') and shipment.dimensions:
            dimensions_display = f"{shipment.dimensions.get('length', '')}x{shipment.dimensions.get('width', '')}x{shipment.dimensions.get('height', '')} cm"
        
        parcel_data = [
            ['Description', 'Weight', 'Dimensions'],
            [
                shipment.goods_description,
                f"{shipment.weight_kg or 0} Kg",
                dimensions_display
            ]
        ]
        
        parcel_table = Table(parcel_data, colWidths=[200, 125, 125])
        parcel_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (2, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (2, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (2, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (2, 1), colors.HexColor('#f5f5f5')),
        ]))
        story.append(parcel_table)
        story.append(Spacer(1, 10))
        
        # ============================================
        # EXPECTED DELIVERY DATE - FIXED DATE HANDLING
        # ============================================
        delivery_date_formatted = format_date_for_pdf(shipment.estimated_delivery_date)
        delivery_text = f"<b>EXPECTED DATE OF DELIVERY: {delivery_date_formatted}</b>"
        delivery_para = Paragraph(delivery_text, styles['CustomCenterAlign'])
        delivery_table = Table([[delivery_para]], colWidths=[450])
        delivery_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (0, 0), (0, 0), 10),
        ]))
        story.append(delivery_table)
        story.append(Spacer(1, 15))
        
        # ============================================
        # TERMS AND CONDITIONS
        # ============================================
        terms_text = """
        Any shortage or damage must be notified within 72 hours of receipt of goods. 
        Complaints can only be accepted if made in writing within 30 days of receipt of goods. 
        No goods may be returned without prior authorization from EukExpress Global Logistics.
        """
        terms_para = Paragraph(terms_text, styles['Italic'])
        terms_table = Table([[terms_para]], colWidths=[450])
        terms_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (0, 0), 8),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#666666')),
        ]))
        story.append(terms_table)
        story.append(Spacer(1, 10))
        
        # ============================================
        # FOOTER
        # ============================================
        footer_text = "EukExpress Global Logistics - Your Trusted Shipping Partner"
        footer_para = Paragraph(footer_text, styles['Italic'])
        footer_table = Table([[footer_para]], colWidths=[450])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (0, 0), 7),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#999999')),
            ('TOPPADDING', (0, 0), (0, 0), 5),
        ]))
        story.append(footer_table)
        
        # ============================================
        # BUILD THE PDF
        # ============================================
        doc.build(story)
        
        # Update shipment with PDF path
        shipment.invoice_pdf_path = pdf_path
        
        logger.info(f"✅ Invoice PDF generated for {shipment.tracking_number} using ReportLab")
        return {"success": True, "path": pdf_path}
        
    except Exception as e:
        logger.error(f"❌ Failed to generate PDF for {shipment.tracking_number}: {e}", exc_info=True)
        return {"success": False, "error": str(e)}