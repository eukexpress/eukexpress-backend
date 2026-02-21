# Eukexpress\backend\scripts\keep_alive_client.py
#!/usr/bin/env python3
"""
Keep-Alive Client Script
Run this as a separate process or cron job to ping the Render app every 10 minutes
"""

import requests
import time
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Your Render app URL
RENDER_APP_URL = os.environ.get('RENDER_APP_URL', 'https://your-app.onrender.com')
PING_INTERVAL = 600  # 10 minutes in seconds

def ping_app():
    """Ping the Render app to keep it alive"""
    try:
        # Ping health endpoint
        response = requests.get(f"{RENDER_APP_URL}/health", timeout=30)
        logger.info(f"Health check: {response.status_code}")
        
        # Also ping public status endpoint
        response = requests.get(f"{RENDER_APP_URL}/api/v1/public/status", timeout=30)
        logger.info(f"Public status: {response.status_code}")
        
        return True
    except Exception as e:
        logger.error(f"Ping failed: {e}")
        return False

def main():
    """Main keep-alive loop"""
    logger.info(f"Starting keep-alive service for {RENDER_APP_URL}")
    logger.info(f"Pinging every {PING_INTERVAL} seconds")
    
    while True:
        ping_app()
        time.sleep(PING_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Keep-alive service stopped")
        sys.exit(0)