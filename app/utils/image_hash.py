# Eukexpress\backend\app\utils\image_hash.py
"""
Perceptual Hashing for Image Duplicate Detection
"""

from PIL import Image
import imagehash
import logging

logger = logging.getLogger(__name__)

def calculate_phash(image_path: str, hash_size: int = 8) -> str:
    """
    Calculate perceptual hash of image
    Returns hash string for duplicate detection
    """
    try:
        image = Image.open(image_path)
        hash_value = str(imagehash.phash(image, hash_size=hash_size))
        return hash_value
    except Exception as e:
        logger.error(f"Failed to calculate phash: {e}")
        return None

def calculate_dhash(image_path: str, hash_size: int = 8) -> str:
    """
    Calculate difference hash (faster than phash)
    Alternative hash method
    """
    try:
        image = Image.open(image_path)
        hash_value = str(imagehash.dhash(image, hash_size=hash_size))
        return hash_value
    except Exception as e:
        logger.error(f"Failed to calculate dhash: {e}")
        return None

def calculate_whash(image_path: str, hash_size: int = 8) -> str:
    """
    Calculate wavelet hash
    Another alternative hash method
    """
    try:
        image = Image.open(image_path)
        hash_value = str(imagehash.whash(image, image_size=hash_size))
        return hash_value
    except Exception as e:
        logger.error(f"Failed to calculate whash: {e}")
        return None

def are_images_similar(hash1: str, hash2: str, threshold: int = 10) -> bool:
    """
    Compare two perceptual hashes
    Returns True if images are similar (Hamming distance < threshold)
    """
    if not hash1 or not hash2:
        return False
    
    # Convert hex strings to integers for comparison
    try:
        h1 = int(hash1, 16)
        h2 = int(hash2, 16)
        # Calculate Hamming distance
        distance = bin(h1 ^ h2).count('1')
        return distance < threshold
    except Exception as e:
        logger.error(f"Failed to compare hashes: {e}")
        return False