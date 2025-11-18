from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.node import YouTubeVideoResponse
from backend.app.services.youtube_service import youtube_service

router = APIRouter()

@router.get("/videos/{video_id}", response_model=YouTubeVideoResponse)
async def get_youtube_video_metadata(
    video_id: str,
):
    """
    Get YouTube video metadata by video ID from the YouTube Data API.
    """
    metadata = await youtube_service.get_video_metadata(video_id=video_id)
    return YouTubeVideoResponse(**metadata)
