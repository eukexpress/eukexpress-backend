"""
External Keep-Alive Cron Job
Run this as a cron job on Render or external service
"""

import requests
import time
import sys
from datetime import datetime

# Your Render app URL
RENDER_APP_URL = "https://eukexpress.onrender.com"
ENDPOINTS = ["/", "/health", "/api/v1/public/status"]

def ping_all():
    """Ping all endpoints"""
    results = []
    
    for endpoint in ENDPOINTS:
        url = f"{RENDER_APP_URL}{endpoint}"
        try:
            start = time.time()
            response = requests.get(url, timeout=10)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - {response.status_code} ({elapsed:.2f}s)")
                results.append(True)
            else:
                print(f"⚠️ {endpoint} - {response.status_code} ({elapsed:.2f}s)")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {endpoint} - Error: {e}")
            results.append(False)
    
    return all(results)

if __name__ == "__main__":
    print(f"\n[{datetime.now().isoformat()}] Running keep-alive ping...")
    success = ping_all()
    
    if success:
        print("✅ All endpoints healthy")
        sys.exit(0)
    else:
        print("⚠️ Some endpoints failed")
        sys.exit(1)