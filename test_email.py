"""
Test Email Configuration
Run with: python test_email.py
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

async def test_email_setup():
    """Test email service configuration"""
    print("\n" + "="*60)
    print("📧 TESTING EMAIL SERVICE CONFIGURATION")
    print("="*60)
    
    # Check API key
    print(f"\n🔑 API Key present: {'✅ YES' if email_service.api_key else '❌ NO'}")
    print(f"📧 From email: {email_service.from_email}")
    print(f"📝 From name: {email_service.from_name}")
    
    # Test sending email
    test_email = input("\n📨 Enter email to send test to: ").strip()
    if test_email:
        print(f"\n📨 Sending test email to {test_email}...")
        result = await email_service.send_test_email(test_email)
        
        if result.get("success"):
            print(f"✅ Test email sent successfully! ID: {result.get('id')}")
        else:
            print(f"❌ Failed to send test email: {result.get('error')}")
    else:
        print("\n⚠️  No email provided, skipping send test")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_email_setup())