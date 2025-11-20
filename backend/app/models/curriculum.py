import uuid
from datetime import datetime, UTC # 1. UTC 임포트
from typing import Optional

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.app.models.base import Base
from backend.app.models.node import Node # Import Node model

class Curriculum(Base):
    __tablename__ = "curriculums"

    curriculum_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    title = Column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Google Drive Integration
    gdrive_folder_id = Column(String(255), nullable=True)

    # 2. lambda와 함께 datetime.now(UTC) 사용
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    nodes = relationship("Node", back_populates="curriculum", cascade="all, delete-orphan") # Add this line
    owner = relationship("User", back_populates="curriculums")

    def __repr__(self):
        return f"<Curriculum(curriculum_id='{self.curriculum_id}', title='{self.title}')>"