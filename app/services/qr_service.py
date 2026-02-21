# Eukexpress\backend\app\services\qr_service.py
"""
QR Code Generation Service
Generates QR codes for tracking
"""

import qrcode
import os
import logging
from PIL import Image

from app.config import settings

logger = logging.getLogger(__name__)

async def generate_qr_code(tracking_number: str) -> str:
    """Generate QR code for tracking number"""
    try:
        # Create QR code directory if it doesn't exist
        os.makedirs(settings.QR_CODE_PATH, exist_ok=True)
        
        # QR code content - tracking URL
        tracking_url = f"{settings.APP_URL}/track?number={tracking_number}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(tracking_url)
        qr.make(fit=True)
        
        # Create image
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Save image
        qr_filename = f"{tracking_number}.png"
        qr_path = os.path.join(settings.QR_CODE_PATH, qr_filename)
        qr_image.save(qr_path)
        
        logger.info(f"QR code generated for {tracking_number}")
        return qr_path
        
    except Exception as e:
        logger.error(f"Failed to generate QR code for {tracking_number}: {e}")
        return None

async def generate_qr_code_with_logo(tracking_number: str, logo_path: str = None) -> str:
    """Generate QR code with logo in center"""
    try:
        # Generate base QR code
        qr_path = await generate_qr_code(tracking_number)
        
        if logo_path and os.path.exists(logo_path):
            # Open QR code and logo
            qr_image = Image.open(qr_path).convert("RGB")
            logo = Image.open(logo_path)
            
            # Calculate logo size (20% of QR code)
            qr_width, qr_height = qr_image.size
            logo_size = int(qr_width * 0.2)
            
            # Resize logo
            logo = logo.resize((logo_size, logo_size))
            
            # Calculate position
            pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
            
            # Paste logo
            qr_image.paste(logo, pos)
            
            # Save with logo
            qr_logo_path = os.path.join(settings.QR_CODE_PATH, f"{tracking_number}-logo.png")
            qr_image.save(qr_logo_path)
            
            logger.info(f"QR code with logo generated for {tracking_number}")
            return qr_logo_path
        
        return qr_path
        
    except Exception as e:
        logger.error(f"Failed to generate QR code with logo for {tracking_number}: {e}")
        return None