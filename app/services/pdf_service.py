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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import qrcode
from io import BytesIO

from app.config import settings

logger = logging.getLogger(__name__)

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
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72,
        )
        
        # Container for the 'Flowable' objects
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='RightAlign',
            parent=styles['Normal'],
            alignment=TA_RIGHT,
        ))
        styles.add(ParagraphStyle(
            name='CenterAlign',
            parent=styles['Normal'],
            alignment=TA_CENTER,
        ))
        styles.add(ParagraphStyle(
            name='Title',
            parent=styles['Heading1'],
            alignment=TA_CENTER,
            textColor=colors.HexColor('#003366'),
            fontSize=24,
            spaceAfter=20,
        ))
        
        # ============================================
        # HEADER with Contact Info
        # ============================================
        header_data = [
            [Paragraph("<b>EukExpress Global Logistics</b>", styles['Title'])],
            [Paragraph("Contact US", styles['RightAlign'])],
            [Paragraph(f"Address: {shipment.sender_address}", styles['RightAlign'])],
            [Paragraph(f"Email: {shipment.sender_email}", styles['RightAlign'])],
        ]
        header_table = Table(header_data, colWidths=[450])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (0, 1), (0, -1), 'RIGHT'),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 20))
        
        # ============================================
        # TRACKING SECTION
        # ============================================
        tracking_data = [
            [Paragraph(f"<b>Tracking ID: {shipment.tracking_number}</b>", styles['Normal'])],
            [Paragraph(f"Date of shipment: {shipment.sending_date.strftime('%d %b, %Y') if shipment.sending_date else 'N/A'}", styles['Normal'])],
        ]
        tracking_table = Table(tracking_data, colWidths=[450])
        tracking_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f5f5f5')),
            ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#f5f5f5')),
            ('LEFTPADDING', (0, 0), (0, -1), 20),
            ('BOTTOMPADDING', (0, 0), (0, 0), 10),
        ]))
        story.append(tracking_table)
        story.append(Spacer(1, 20))
        
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
            [Paragraph(sender_text, styles['Normal']), 
             Paragraph(receiver_text, styles['Normal'])]
        ]
        
        parties_table = Table(parties_data, colWidths=[225, 225])
        parties_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#e0e0e0')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 15),
            ('RIGHTPADDING', (0, 0), (-1, -1), 15),
            ('TOPPADDING', (0, 0), (-1, -1), 15),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ]))
        story.append(parties_table)
        story.append(Spacer(1, 20))
        
        # ============================================
        # DESTINATION
        # ============================================
        dest_text = f"<b>Destination: {shipment.destination_location}</b>"
        story.append(Paragraph(dest_text, styles['Normal']))
        story.append(Spacer(1, 10))
        
        # ============================================
        # COMMENTS / AMOUNT
        # ============================================
        comment_text = f"<b>Comments: {shipment.declared_currency} {shipment.declared_value or 0}</b>"
        comment_para = Paragraph(comment_text, styles['Normal'])
        comment_table = Table([[comment_para]], colWidths=[450])
        comment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#fff3cd')),
            ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#ffeeba')),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('LEFTPADDING', (0, 0), (0, 0), 15),
            ('TOPPADDING', (0, 0), (0, 0), 10),
            ('BOTTOMPADDING', (0, 0), (0, 0), 10),
        ]))
        story.append(comment_table)
        story.append(Spacer(1, 20))
        
        # ============================================
        # PARCEL DESCRIPTION
        # ============================================
        story.append(Paragraph("<b>PARCEL DESCRIPTION</b>", styles['Normal']))
        story.append(Spacer(1, 10))
        
        # Format dimensions
        dimensions_display = "N/A"
        if shipment.dimensions:
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
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 1), (2, 1), colors.HexColor('#f5f5f5')),
        ]))
        story.append(parcel_table)
        story.append(Spacer(1, 20))
        
        # ============================================
        # EXPECTED DELIVERY DATE
        # ============================================
        delivery_text = f"<b>EXPECTED DATE OF DELIVERY: {shipment.estimated_delivery_date.strftime('%d %b %Y') if shipment.estimated_delivery_date else 'N/A'}</b>"
        delivery_para = Paragraph(delivery_text, styles['CenterAlign'])
        delivery_table = Table([[delivery_para]], colWidths=[450])
        delivery_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#003366')),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('TOPPADDING', (0, 0), (0, 0), 15),
            ('BOTTOMPADDING', (0, 0), (0, 0), 15),
        ]))
        story.append(delivery_table)
        story.append(Spacer(1, 30))
        
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
            ('FONTSIZE', (0, 0), (0, 0), 9),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#666666')),
        ]))
        story.append(terms_table)
        story.append(Spacer(1, 20))
        
        # ============================================
        # QR CODE (Generated on the fly)
        # ============================================
        try:
            # Generate QR code pointing to frontend tracking page
            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://eukexpress.com')
            qr_data = f"{frontend_url}/track.html?number={shipment.tracking_number}"
            
            # Create QR code image
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert PIL image to bytes for ReportLab
            img_buffer = BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Create ReportLab Image
            qr_reportlab = Image(img_buffer, width=1.5*inch, height=1.5*inch)
            
            # Create a table to hold the QR code (right-aligned)
            qr_data = [[qr_reportlab]]
            qr_table = Table(qr_data, colWidths=[450])
            qr_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ]))
            story.append(qr_table)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not generate QR code: {e}")
        
        # ============================================
        # FOOTER
        # ============================================
        footer_text = "EukExpress Global Logistics - Your Trusted Shipping Partner"
        footer_para = Paragraph(footer_text, styles['Italic'])
        footer_table = Table([[footer_para]], colWidths=[450])
        footer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (0, 0), 8),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#999999')),
            ('TOPPADDING', (0, 0), (0, 0), 20),
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