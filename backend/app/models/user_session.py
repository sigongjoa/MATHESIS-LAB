"""
User Session Model for MATHESIS LAB

Tracks active user sessions with refresh token management.
"""

import uuid
from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class UserSession(Base):
    """
    User Session Model

    Tracks active user sessions for managing refresh tokens and
    implementing token revocation and logout functionality.
    """

    __tablename__ = "user_sessions"

    # Primary key
    session_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key to user
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)

    # Refresh token hash (never store plain tokens)
    refresh_token_hash = Column(String(255), nullable=False, unique=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)  # When refresh token expires
    revoked_at: Column[Optional[DateTime]] = Column(DateTime, nullable=True)  # When token was revoked/invalidated

    # Relationship
    user = relationship("User", back_populates="sessions")

    # Indexes
    __table_args__ = (
        Index("idx_user_session_user_id", "user_id"),
        Index("idx_user_session_created_at", "created_at"),
        Index("idx_user_session_expires_at", "expires_at"),
    )

    def __repr__(self):
        return f"<UserSession(session_id='{self.session_id}', user_id='{self.user_id}')>"

    def is_valid(self) -> bool:
        """
        Check if session is still valid.

        Returns:
            True if session is not revoked and not expired
        """
        now = datetime.now(UTC)
        return self.revoked_at is None and now < self.expires_at

    def is_expired(self) -> bool:
        """
        Check if session has expired.

        Returns:
            True if expiration time has passed
        """
        now = datetime.now(UTC)
        return now >= self.expires_at

    def is_revoked(self) -> bool:
        """
        Check if session has been revoked.

        Returns:
            True if revoked_at is set
        """
        return self.revoked_at is not None

    def to_dict(self):
        """
        Convert session to dictionary.

        Returns:
            Dictionary representation of session (excludes token hash for security)
        """
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "is_valid": self.is_valid(),
            "is_expired": self.is_expired(),
            "is_revoked": self.is_revoked(),
        }
