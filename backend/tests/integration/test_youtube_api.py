import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from backend.app.core.config import settings
from backend.app.services.youtube_service import youtube_service

def test_get_youtube_video_metadata_success(client: TestClient, mocker):
    """
    Test successful retrieval of YouTube video metadata.
    """
    settings.YOUTUBE_API_KEY = "mock_youtube_api_key"

    mock_metadata = {
        "video_id": "dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up (Official Music Video)",
        "channel_title": "RickAstley",
        "description": "The official video for “Never Gonna Give You Up” by Rick Astley",
        "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        "duration_seconds": 212,
        "published_at": "1987-07-27T00:00:00Z",
    }

    mocker.patch.object(
        youtube_service,
        "get_video_metadata",
        new_callable=AsyncMock,
        return_value=mock_metadata
    )

    response = client.get("/api/v1/youtube/videos/dQw4w9WgXcQ")
    
    assert response.status_code == 200
    metadata = response.json()
    assert metadata["video_id"] == "dQw4w9WgXcQ"
    assert metadata["title"] == "Rick Astley - Never Gonna Give You Up (Official Music Video)"
    assert metadata["duration_seconds"] == 212
    
    youtube_service.get_video_metadata.assert_called_once_with(video_id="dQw4w9WgXcQ")

def test_get_youtube_video_metadata_no_api_key(client: TestClient, mocker):
    """
    Test retrieval when YouTube API key is not configured.
    """
    settings.YOUTUBE_API_KEY = None

    mocker.patch.object(
        youtube_service,
        "get_video_metadata",
        new_callable=AsyncMock,
        side_effect=ValueError("YouTube API key is not configured.")
    )

    response = client.get("/api/v1/youtube/videos/some_id")
    assert response.status_code == 400
    assert "YouTube API key is not configured." in response.json()["detail"]

def test_get_youtube_video_metadata_video_not_found(client: TestClient, mocker):
    """
    Test retrieval when video is not found.
    """
    settings.YOUTUBE_API_KEY = "mock_youtube_api_key"

    mocker.patch.object(
        youtube_service,
        "get_video_metadata",
        new_callable=AsyncMock,
        side_effect=ValueError("No video found for ID: non_existent_id")
    )

    response = client.get("/api/v1/youtube/videos/non_existent_id")
    assert response.status_code == 400
    assert "No video found for ID: non_existent_id" in response.json()["detail"]

def test_get_youtube_video_metadata_service_error(client: TestClient, mocker):
    """
    Test retrieval when YouTubeService encounters an error.
    """
    settings.YOUTUBE_API_KEY = "mock_youtube_api_key"

    mocker.patch.object(
        youtube_service,
        "get_video_metadata",
        new_callable=AsyncMock,
        side_effect=RuntimeError("YouTube API is temporarily unavailable")
    )

    response = client.get("/api/v1/youtube/videos/some_id")
    assert response.status_code == 500
    assert "YouTube API is temporarily unavailable" in response.json()["detail"]
