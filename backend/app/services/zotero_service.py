import httpx
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings

class ZoteroService:
    def __init__(self):
        self.base_url = settings.ZOTERO_API_BASE_URL
        self.api_key = settings.ZOTERO_API_KEY
        self.client = httpx.AsyncClient()

    async def get_items_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        if not self.base_url:
            raise ValueError("Zotero API base URL is not configured.")
        
        # Assuming a simple endpoint for tag-based search on a self-hosted Zotero instance
        # This might need adjustment based on the actual Zotero API implementation
        url = f"{self.base_url}/items?tag={tag}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}" # Or other auth method

        try:
            response = await self.client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status() # Raise an exception for 4xx or 5xx status codes
            return response.json()
        except httpx.RequestError as e:
            raise RuntimeError(f"Zotero API request failed: {e}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Zotero API returned an error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during Zotero API call: {e}")

    async def get_item_by_key(self, zotero_key: str) -> Dict[str, Any]:
        if not self.base_url:
            raise ValueError("Zotero API base URL is not configured.")
        
        url = f"{self.base_url}/items/{zotero_key}"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self.client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise RuntimeError(f"Zotero API request failed: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ValueError(f"Zotero item with key '{zotero_key}' not found.")
            raise RuntimeError(f"Zotero API returned an error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during Zotero API call: {e}")

# Initialize Zotero service globally
zotero_service = ZoteroService()
