import uuid
from datetime import datetime, UTC

from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # Import as PG_UUID to avoid name collision

from backend.app.models.base import Base

class YouTubeVideo(Base):
    __tablename__ = "youtube_videos"

    youtube_video_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    video_id = Column(String(20), unique=True, nullable=False)
    title = Column(String(512), nullable=False)
    channel_title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self):
        return f"<YouTubeVideo(youtube_video_id='{self.youtube_video_id}', title='{self.title}')>"
