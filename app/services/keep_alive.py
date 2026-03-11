"""
Keep-Alive Service for Render Free Tier
Pings the application every 10 minutes to prevent sleeping
"""

import asyncio
import logging
import httpx
from datetime import datetime
from typing import Optional, List
import time

from app.config import settings

logger = logging.getLogger(__name__)

class KeepAliveService:
    """
    Service to keep the application alive on Render free tier
    Pings the app every 10 minutes to prevent the 15-minute idle timeout
    """
    
    def __init__(self, app_url: Optional[str] = None):
        self.app_url = app_url or settings.RENDER_APP_URL
        self.endpoints = settings.keep_alive_endpoints_list
        self.ping_interval = settings.KEEP_ALIVE_INTERVAL * 60  # Convert to seconds
        self.is_running = False
        self.ping_count = 0
        self.successful_pings = 0
        self.failed_pings = 0
        self.client = None
    
    async def init_client(self):
        """Initialize HTTP client"""
        if not self.client:
            self.client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
    
    async def ping_endpoint(self, endpoint: str) -> dict:
        """Ping a single endpoint and return result"""
        url = f"{self.app_url}{endpoint}"
        start_time = time.time()
        
        try:
            await self.init_client()
            response = await self.client.get(url)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "elapsed": round(elapsed, 3)
                }
            else:
                return {
                    "success": False,
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "elapsed": round(elapsed, 3)
                }
                
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                "success": False,
                "endpoint": endpoint,
                "error": str(e),
                "elapsed": round(elapsed, 3)
            }
    
    async def ping_all_endpoints(self) -> List[dict]:
        """Ping all configured endpoints concurrently"""
        tasks = [self.ping_endpoint(endpoint) for endpoint in self.endpoints]
        results = await asyncio.gather(*tasks)
        
        self.ping_count += 1
        
        # Count successes and failures
        for result in results:
            if result.get("success"):
                self.successful_pings += 1
            else:
                self.failed_pings += 1
        
        # Log summary
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(
            f"📊 Keep-alive ping #{self.ping_count} - "
            f"Success: {success_count}/{len(results)} - "
            f"Total: {self.successful_pings} ok, {self.failed_pings} failed"
        )
        
        return results
    
    async def run(self):
        """Run the keep-alive service continuously"""
        self.is_running = True
        logger.info(
            f"🚀 Keep-alive service started. "
            f"Pinging {len(self.endpoints)} endpoints every {settings.KEEP_ALIVE_INTERVAL} minutes"
        )
        
        # Do initial ping immediately
        await self.ping_all_endpoints()
        
        while self.is_running:
            # Wait for next interval
            for _ in range(self.ping_interval):
                if not self.is_running:
                    break
                await asyncio.sleep(1)
            
            if self.is_running:
                await self.ping_all_endpoints()
    
    async def stop(self):
        """Stop the keep-alive service"""
        self.is_running = False
        if self.client:
            await self.client.aclose()
        logger.info(
            f"🛑 Keep-alive service stopped. "
            f"Total pings: {self.ping_count}, "
            f"Success: {self.successful_pings}, Failed: {self.failed_pings}"
        )

# Global instance
keep_alive_service = KeepAliveService()

async def start_keep_alive():
    """Start the keep-alive service in the background"""
    asyncio.create_task(keep_alive_service.run())