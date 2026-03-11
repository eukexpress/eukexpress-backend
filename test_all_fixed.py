"""
Test script to verify all fixes
Run with: python test_all_fixed.py
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.services.email_service import email_service
from app.services.pdf_service import generate_invoice_pdf

async def test_all():
    """Test all fixed components"""
    print("\n" + "="*60)
    print("🧪 TESTING ALL FIXES")
    print("="*60)
    
    # 1. Test email configuration
    print("\n📧 1. TESTING EMAIL CONFIGURATION")
    print("-" * 40)
    print(f"API Key present: {'✅ YES' if email_service.api_key else '❌ NO'}")
    print(f"From email raw: {email_service.from_email}")
    print(f"From name: {email_service.from_name}")
    
    formatted = email_service._format_from_address()
    print(f"Formatted from: {formatted}")
    
    if '<' in formatted and '>' in formatted:
        print("✅ Email format is correct (Name <email>)")
    else:
        print("❌ Email format is incorrect")
    
    # 2. Test PDF configuration
    print("\n📄 2. TESTING PDF CONFIGURATION")
    print("-" * 40)
    print(f"QR_CODE_PATH: {settings.QR_CODE_PATH}")
    print(f"UPLOAD_PATH: {settings.UPLOAD_PATH}")
    print(f"APP_URL: {settings.APP_URL}")
    
    # Check if directories exist
    if os.path.exists(settings.QR_CODE_PATH):
        print(f"✅ QR code directory exists")
    else:
        print(f"⚠️ QR code directory does not exist (will be created)")
    
    if os.path.exists(settings.UPLOAD_PATH):
        print(f"✅ Upload directory exists")
    else:
        print(f"⚠️ Upload directory does not exist (will be created)")
    
    # 3. Test JWT settings
    print("\n🔐 3. TESTING JWT SETTINGS")
    print("-" * 40)
    print(f"JWT expiry: {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    print(f"Session expiry: {settings.SESSION_EXPIRE_MINUTES} minutes")
    print(f"Environment: {settings.APP_ENV}")
    
    if settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES >= 1440:
        print("✅ JWT expiry is set to 24 hours")
    else:
        print(f"⚠️ JWT expiry is only {settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
    
    # 4. Send test email (optional)
    print("\n📨 4. SEND TEST EMAIL")
    print("-" * 40)
    test_email = input("Enter email to send test to (or press Enter to skip): ").strip()
    if test_email:
        print(f"Sending test email to {test_email}...")
        result = await email_service.send_test_email(test_email)
        if result.get("success"):
            print(f"✅ Test email sent! ID: {result.get('id')}")
        else:
            print(f"❌ Failed: {result.get('error')}")
    else:
        print("Skipping email test")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_all())
