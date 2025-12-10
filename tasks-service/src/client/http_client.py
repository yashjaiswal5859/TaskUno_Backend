"""
HTTP client for inter-service communication.
"""
import httpx
from typing import Optional, Dict, Any
from src.config.settings import settings


class ServiceClient:
    """HTTP client for calling other microservices."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
    
    async def get(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make GET request to service."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def post(self, endpoint: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make POST request to service."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def put(self, endpoint: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make PUT request to service."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def delete(self, endpoint: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make DELETE request to service."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(url, headers=headers)
            response.raise_for_status()
            return response.json() if response.content else {}


# Service client instances
organization_client = ServiceClient(settings.ORGANIZATION_SERVICE_URL)



