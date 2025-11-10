import uuid
from datetime import datetime, UTC # 1. UTC 임포트

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import relationship

from backend.app.models.base import Base
from backend.app.models.node import Node # Import Node model

class Curriculum(Base):
    __tablename__ = "curriculums"

    curriculum_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # 2. lambda와 함께 datetime.now(UTC) 사용
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    nodes = relationship("Node", back_populates="curriculum", cascade="all, delete-orphan") # Add this line

    def __repr__(self):
        return f"<Curriculum(curriculum_id='{self.curriculum_id}', title='{self.title}')>"