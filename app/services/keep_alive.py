# Eukexpress\backend\app\services\keep_alive.py
"""
Keep-Alive Service for Render Free Tier
Pings the application every 10 minutes to prevent sleeping
"""

import asyncio
import logging
import httpx
from datetime import datetime
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

class KeepAliveService:
    """
    Service to keep the application alive on Render free tier
    Pings the app every 10 minutes to prevent the 15-minute idle timeout
    """
    
    def __init__(self, app_url: Optional[str] = None):
        self.app_url = app_url or settings.APP_URL
        self.ping_interval = 600  # 10 minutes in seconds
        self.is_running = False
        self.ping_count = 0
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def ping_self(self):
        """Ping the application to keep it alive"""
        try:
            # Ping the health endpoint
            response = await self.client.get(f"{self.app_url}/health")
            self.ping_count += 1
            logger.info(f"Keep-alive ping #{self.ping_count} at {datetime.utcnow().isoformat()} - Status: {response.status_code}")
            
            # Also ping a few other endpoints to ensure all modules are loaded
            await self.client.get(f"{self.app_url}/api/v1/public/status")
            
            return True
        except Exception as e:
            logger.error(f"Keep-alive ping failed: {e}")
            return False
    
    async def run(self):
        """Run the keep-alive service continuously"""
        self.is_running = True
        logger.info(f"Keep-alive service started. Pinging every {self.ping_interval} seconds")
        
        while self.is_running:
            await self.ping_self()
            await asyncio.sleep(self.ping_interval)
    
    def stop(self):
        """Stop the keep-alive service"""
        self.is_running = False
        logger.info("Keep-alive service stopped")

# Global instance
keep_alive_service = KeepAliveService()

async def start_keep_alive():
    """Start the keep-alive service in the background"""
    asyncio.create_task(keep_alive_service.run())