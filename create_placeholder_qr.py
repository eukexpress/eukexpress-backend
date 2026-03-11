"""
Create placeholder QR code image for when real QR codes are missing
Run this script once to create the placeholder
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_placeholder_qr(output_path: str, size: int = 300):
    """
    Create a placeholder QR code image
    
    Args:
        output_path: Where to save the image
        size: Image size in pixels
    """
    # Create white background
    img = Image.new('RGB', (size, size), color='white')
    draw = ImageDraw.Draw(img)
    
    # Draw border
    border_width = 5
    draw.rectangle(
        [(0, 0), (size-1, size-1)], 
        outline='#003366', 
        width=border_width
    )
    
    # Draw QR-like pattern
    block_size = size // 10
    for i in range(0, size, block_size * 2):
        # Horizontal lines
        draw.rectangle(
            [i, block_size, i + block_size, block_size * 2],
            fill='#003366'
        )
        # Vertical lines
        draw.rectangle(
            [block_size, i, block_size * 2, i + block_size],
            fill='#003366'
        )
    
    # Draw corner markers (like real QR codes)
    corner_size = block_size * 3
    # Top-left corner
    draw.rectangle(
        [10, 10, 10 + corner_size, 10 + corner_size],
        outline='#003366',
        width=3
    )
    draw.rectangle(
        [15, 15, 5 + corner_size, 5 + corner_size],
        outline='#003366',
        width=2
    )
    
    # Top-right corner
    draw.rectangle(
        [size - 10 - corner_size, 10, size - 10, 10 + corner_size],
        outline='#003366',
        width=3
    )
    
    # Bottom-left corner
    draw.rectangle(
        [10, size - 10 - corner_size, 10 + corner_size, size - 10],
        outline='#003366',
        width=3
    )
    
    # Add text
    try:
        # Try to use a font if available
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        # Fall back to default
        font = ImageFont.load_default()
    
    # Draw "EUK" text
    text = "EUK"
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_x = (size - text_width) // 2
    draw.text((text_x, size//2 - 15), text, fill='#003366', font=font)
    
    # Draw "EXPRESS" text
    text2 = "EXPRESS"
    text2_bbox = draw.textbbox((0, 0), text2, font=font)
    text2_width = text2_bbox[2] - text2_bbox[0]
    text2_x = (size - text2_width) // 2
    draw.text((text2_x, size//2 + 15), text2, fill='#003366', font=font)
    
    # Save the image
    img.save(output_path, 'PNG')
    print(f"✅ Placeholder QR code created at: {output_path}")
    
    return output_path

if __name__ == "__main__":
    # For local development
    local_path = os.path.join(os.path.dirname(__file__), "frontend", "qr_codes", "placeholder.png")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    create_placeholder_qr(local_path)
    
    # For Render deployment path
    render_path = "/opt/render/project/src/frontend/qr_codes/placeholder.png"
    os.makedirs(os.path.dirname(render_path), exist_ok=True)
    create_placeholder_qr(render_path)
    
    print("\n" + "="*50)
    print("✅ Placeholder QR codes created for both:")
    print(f"   • Local: {local_path}")
    print(f"   • Render: {render_path}")
    print("="*50)