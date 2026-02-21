# Eukexpress\backend\app\services\image_service.py
"""
Image Validation and Storage Service
Handles image uploads, validation, and duplicate detection
"""

import os
import hashlib
import logging
from PIL import Image
import imagehash
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png']
MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE

def validate_image(file) -> dict:
    """Validate image file size and type"""
    try:
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset position
        
        if file_size > MAX_FILE_SIZE:
            return {
                "success": False,
                "error": f"File size exceeds {MAX_FILE_SIZE // 1048576}MB limit"
            }
        
        # Check file extension
        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            return {
                "success": False,
                "error": f"File type {ext} not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }
        
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Image validation error: {e}")
        return {"success": False, "error": str(e)}

def calculate_image_hash(image_path: str) -> str:
    """Calculate perceptual hash of image for duplicate detection"""
    try:
        image = Image.open(image_path)
        hash_value = str(imagehash.phash(image))
        return hash_value
    except Exception as e:
        logger.error(f"Hash calculation error: {e}")
        return None

async def save_image(file, tracking_number: str, position: str) -> dict:
    """Save uploaded image to filesystem"""
    try:
        # Validate image
        validation = validate_image(file)
        if not validation["success"]:
            return validation
        
        # Create shipment directory
        shipment_dir = os.path.join(settings.UPLOAD_PATH, "shipments", tracking_number)
        thumb_dir = os.path.join(shipment_dir, "thumbnails")
        os.makedirs(shipment_dir, exist_ok=True)
        os.makedirs(thumb_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = os.path.splitext(file.filename)[1].lower()
        filename = f"{position}_{timestamp}{ext}"
        filepath = os.path.join(shipment_dir, filename)
        
        # Save original image
        contents = await file.read()
        with open(filepath, "wb") as f:
            f.write(contents)
        
        # Calculate perceptual hash
        image_hash = calculate_image_hash(filepath)
        
        # Create thumbnail
        create_thumbnail(filepath, os.path.join(thumb_dir, filename))
        
        logger.info(f"Image saved: {filepath}")
        
        return {
            "success": True,
            "path": f"/uploads/shipments/{tracking_number}/{filename}",
            "hash": image_hash,
            "filename": filename
        }
        
    except Exception as e:
        logger.error(f"Failed to save image: {e}")
        return {"success": False, "error": str(e)}

def create_thumbnail(image_path: str, thumb_path: str, size: tuple = (300, 300)):
    """Create thumbnail of image"""
    try:
        image = Image.open(image_path)
        image.thumbnail(size, Image.Resampling.LANCZOS)
        image.save(thumb_path)
        logger.debug(f"Thumbnail created: {thumb_path}")
    except Exception as e:
        logger.error(f"Failed to create thumbnail: {e}")

def check_duplicate_images(db, front_hash: str, rear_hash: str) -> bool:
    """Check if images already exist in database"""
    from app.models import Shipment
    
    # Check for identical images
    front_exists = db.query(Shipment).filter(
        (Shipment.front_image_hash == front_hash) | 
        (Shipment.rear_image_hash == front_hash)
    ).first()
    
    rear_exists = db.query(Shipment).filter(
        (Shipment.front_image_hash == rear_hash) | 
        (Shipment.rear_image_hash == rear_hash)
    ).first()
    
    return front_exists is not None or rear_exists is not None