"""
PDF Utilities
Helper functions for PDF generation - COMPLETE FIXED VERSION
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Union
from weasyprint import HTML
import base64

logger = logging.getLogger(__name__)

def ensure_directory_exists(directory_path: str) -> None:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        directory_path: Path to directory to create
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        logger.debug(f"✅ Directory ensured: {directory_path}")
    except Exception as e:
        logger.error(f"❌ Failed to create directory {directory_path}: {e}")
        raise

def generate_pdf_filename(tracking_number: str, prefix: str = "invoice") -> str:
    """
    Generate standardized PDF filename
    
    Args:
        tracking_number: Shipment tracking number
        prefix: Prefix for filename (default: invoice)
    
    Returns:
        Formatted filename: {prefix}-{tracking_number}.pdf
    """
    return f"{prefix}-{tracking_number}.pdf"

def get_qr_code_path(qr_code_dir: str, tracking_number: str) -> str:
    """
    Get QR code file path with fallback to placeholder
    
    Args:
        qr_code_dir: Directory containing QR codes
        tracking_number: Shipment tracking number
    
    Returns:
        Absolute path to QR code image or placeholder
    """
    # Try specific QR code
    qr_path = os.path.join(qr_code_dir, f"{tracking_number}.png")
    
    if os.path.exists(qr_path):
        logger.debug(f"✅ Found QR code: {qr_path}")
        return qr_path
    
    # Try placeholder
    placeholder = os.path.join(qr_code_dir, "placeholder.png")
    if os.path.exists(placeholder):
        logger.warning(f"⚠️ QR code not found for {tracking_number}, using placeholder")
        return placeholder
    
    logger.error(f"❌ No QR code or placeholder found for {tracking_number}")
    return ""

def format_qr_code_url(qr_code_path: str) -> str:
    """
    Format QR code path as file:// URL for WeasyPrint
    
    Args:
        qr_code_path: Absolute path to QR code image
    
    Returns:
        file:// URL or empty string if path is empty
    """
    if not qr_code_path:
        return ""
    return f"file://{qr_code_path}"

def html_to_pdf(
    html_content: str, 
    output_path: str, 
    base_url: Optional[str] = None
) -> bool:
    """
    Convert HTML to PDF with error handling - FIXED for WeasyPrint 60.1 compatibility
    
    Args:
        html_content: HTML string to convert
        output_path: Path where PDF should be saved
        base_url: Base URL for resolving relative URLs
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # For WeasyPrint 60.1, we need to use a different approach
        # Create HTML object first
        if base_url:
            html = HTML(string=html_content, base_url=base_url)
        else:
            html = HTML(string=html_content)
        
        # Write PDF - don't pass any extra arguments
        html.write_pdf(output_path)
        
        logger.info(f"✅ PDF generated: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ PDF conversion failed: {e}", exc_info=True)
        return False

def format_dimensions(dimensions: Optional[Dict[str, float]]) -> str:
    """
    Format dimensions dictionary for display
    
    Args:
        dimensions: Dictionary with length, width, height keys
    
    Returns:
        Formatted string like "10x20x30 cm" or "N/A"
    """
    if not dimensions:
        return "N/A"
    
    try:
        length = dimensions.get('length', '')
        width = dimensions.get('width', '')
        height = dimensions.get('height', '')
        
        if length and width and height:
            return f"{length}x{width}x{height} cm"
        return "N/A"
    except Exception as e:
        logger.error(f"Error formatting dimensions: {e}")
        return "N/A"

def format_currency(amount: Optional[float], currency: str = "USD") -> str:
    """
    Format currency amount for display
    
    Args:
        amount: Numeric amount
        currency: Currency code (USD, EUR, etc.)
    
    Returns:
        Formatted currency string
    """
    if amount is None:
        return "N/A"
    
    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "NGN": "₦"
    }
    symbol = symbols.get(currency, "")
    
    try:
        return f"{symbol}{amount:,.2f}"
    except:
        return f"{symbol}{amount}"

def get_pdf_path(invoice_dir: str, tracking_number: str) -> str:
    """
    Get full PDF path for a shipment
    
    Args:
        invoice_dir: Directory for invoices
        tracking_number: Shipment tracking number
    
    Returns:
        Full path to PDF file
    """
    filename = generate_pdf_filename(tracking_number)
    return os.path.join(invoice_dir, filename)

def read_qr_code_file(qr_code_dir: str, tracking_number: str) -> Optional[bytes]:
    """
    Read QR code file as bytes for email attachment
    
    Args:
        qr_code_dir: Directory containing QR codes
        tracking_number: Shipment tracking number
    
    Returns:
        QR code file content as bytes, or None if not found
    """
    qr_path = get_qr_code_path(qr_code_dir, tracking_number)
    if qr_path and os.path.exists(qr_path):
        try:
            with open(qr_path, 'rb') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read QR code file: {e}")
            return None
    return None

def encode_file_for_email(file_content: bytes) -> str:
    """
    Encode file content for email attachment (Resend expects base64)
    
    Args:
        file_content: Binary file content
    
    Returns:
        Base64 encoded string
    """
    return base64.b64encode(file_content).decode('utf-8')