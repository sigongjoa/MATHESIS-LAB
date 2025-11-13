import httpx
from typing import Dict, Any, Optional
from backend.app.core.config import settings

class YouTubeService:
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.client = httpx.AsyncClient()

    async def get_video_metadata(self, video_id: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("YouTube API key is not configured.")
        
        url = f"{self.base_url}/videos"
        params = {
            "id": video_id,
            "key": self.api_key,
            "part": "snippet,contentDetails" # Request snippet and contentDetails for metadata
        }

        try:
            response = await self.client.get(url, params=params, timeout=10.0)
            response.raise_for_status()
            data = response.json()

            if not data.get("items"):
                raise ValueError(f"No video found for ID: {video_id}")

            item = data["items"][0]
            snippet = item["snippet"]
            content_details = item["contentDetails"]

            # Parse duration from ISO 8601 format (e.g., PT1H30M15S) to seconds
            duration_iso = content_details.get("duration", "PT0S")
            duration_seconds = self._parse_youtube_duration(duration_iso)

            return {
                "video_id": video_id,
                "title": snippet.get("title"),
                "channel_title": snippet.get("channelTitle"),
                "description": snippet.get("description"),
                "thumbnail_url": snippet.get("thumbnails", {}).get("high", {}).get("url"),
                "duration_seconds": duration_seconds,
                "published_at": snippet.get("publishedAt"),
            }
        except httpx.RequestError as e:
            raise RuntimeError(f"YouTube API request failed: {e}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"YouTube API returned an error: {e.response.status_code} - {e.response.text}")
        except ValueError as e:
            raise e # Re-raise specific ValueErrors
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred during YouTube API call: {e}")

    def _parse_youtube_duration(self, duration_iso: str) -> int:
        """Parses ISO 8601 duration string (e.g., PT1H30M15S) to total seconds."""
        # This is a simplified parser. For full ISO 8601, a library like isodate might be needed.
        total_seconds = 0
        if "H" in duration_iso:
            hours = int(duration_iso.split("H")[0].replace("PT", ""))
            total_seconds += hours * 3600
            duration_iso = duration_iso.split("H")[1]
        if "M" in duration_iso:
            minutes = int(duration_iso.split("M")[0].replace("PT", ""))
            total_seconds += minutes * 60
            duration_iso = duration_iso.split("M")[1]
        if "S" in duration_iso:
            seconds = int(duration_iso.split("S")[0].replace("PT", ""))
            total_seconds += seconds
        return total_seconds

# Initialize YouTube service globally
youtube_service = YouTubeService()
