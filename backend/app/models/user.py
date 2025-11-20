"""
User Model for MATHESIS LAB

Represents a user account with authentication and profile information.
"""

import uuid
from datetime import datetime, UTC
from typing import Optional, List

from sqlalchemy import Column, String, Boolean, DateTime, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from backend.app.models.base import Base


class User(Base):
    """
    User Model

    Represents a user account with email, password, and profile information.
    Supports both username/password and OAuth authentication.
    """

    __tablename__ = "users"

    # Primary key
    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Core authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)

    # Password (NULL if using OAuth)
    password_hash = Column(String(255), nullable=True)

    # Profile information
    profile_picture_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # User status and permissions
    role = Column(String(50), default="user", nullable=False)  # 'user', 'admin', 'moderator'
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    last_login: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    # Google Drive OAuth tokens
    gdrive_access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gdrive_refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gdrive_token_expiry: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    # Soft delete
    deleted_at: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    curriculums = relationship("Curriculum", back_populates="owner")

    # Indexes
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_is_active", "is_active"),
        Index("idx_user_created_at", "created_at"),
        UniqueConstraint("email", name="uq_user_email"),
    )

    def __repr__(self):
        return f"<User(user_id='{self.user_id}', email='{self.email}', name='{self.name}')>"

    def to_dict(self, include_password=False):
        """
        Convert user to dictionary.

        Args:
            include_password: Whether to include password_hash (should be False for API responses)

        Returns:
            Dictionary representation of user
        """
        data = {
            "user_id": self.user_id,
            "email": self.email,
            "name": self.name,
            "profile_picture_url": self.profile_picture_url,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        if include_password:
            data["password_hash"] = self.password_hash
        return data
