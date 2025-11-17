"""
Sync Metadata Models for Google Drive Integration

Tracks synchronization state between local SQLite database and Google Drive.
"""

import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from backend.app.models.base import Base


class SyncMetadata(Base):
    """
    Tracks synchronization metadata for nodes between local DB and Google Drive.

    Each node can have one SyncMetadata record that tracks:
    - Which Google Drive file it corresponds to
    - When it was last synced locally and on Drive
    - Current sync status (synced, pending, conflict)
    """
    __tablename__ = "sync_metadata"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    curriculum_id = Column(String, ForeignKey("curriculums.curriculum_id"), nullable=False)
    node_id = Column(String, ForeignKey("nodes.node_id"), nullable=False, unique=True)

    # Google Drive file reference
    google_drive_file_id = Column(String, nullable=True)
    google_drive_folder_id = Column(String, nullable=True)

    # Sync timestamps
    last_local_modified = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    last_drive_modified = Column(DateTime, nullable=True)
    last_sync_time = Column(DateTime, nullable=True)

    # Sync status tracking
    sync_status = Column(String(20), default="pending", nullable=False)  # pending, synced, conflict, failed
    is_synced = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    curriculum = relationship("Curriculum")
    node = relationship("Node")

    def __repr__(self):
        return f"<SyncMetadata(id='{self.id}', node_id='{self.node_id}', status='{self.sync_status}')>"


class CurriculumDriveFolder(Base):
    """
    Maps local Curriculum to Google Drive folder.

    Maintains the relationship between curriculum and its corresponding
    Drive folder for organizing nodes hierarchically on Drive.
    """
    __tablename__ = "curriculum_drive_folders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    curriculum_id = Column(String, ForeignKey("curriculums.curriculum_id"), nullable=False, unique=True)
    google_drive_folder_id = Column(String, nullable=False)

    # Track when folder was created and last synced
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    last_sync_at = Column(DateTime, nullable=True)

    curriculum = relationship("Curriculum")

    def __repr__(self):
        return f"<CurriculumDriveFolder(curriculum_id='{self.curriculum_id}', folder_id='{self.google_drive_folder_id}')>"


class GoogleDriveToken(Base):
    """
    Stores Google Drive OAuth tokens for authenticated users.

    Manages access and refresh tokens for Drive API access,
    allowing offline access and automatic token refresh.
    """
    __tablename__ = "google_drive_tokens"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)  # Optional user association

    access_token = Column(String, nullable=False)
    refresh_token = Column(String, nullable=True)
    token_expiry = Column(DateTime, nullable=True)

    # Token metadata
    token_type = Column(String, default="Bearer", nullable=False)
    scope = Column(String, nullable=True)

    # Track token validity
    is_valid = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self):
        return f"<GoogleDriveToken(id='{self.id}', is_valid={self.is_valid})>"
