"""
GCP Vertex AI Service for MATHESIS LAB

Handles Google Cloud Platform integrations:
- Vertex AI (non-Gemini features)
- Cloud Storage integration
- Multi-device sync support
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from google.cloud import aiplatform
from google.cloud import storage
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
GCP_AVAILABLE = True

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class GCPService:
    """Manages GCP integrations for MATHESIS LAB."""

    def __init__(self):
        """Initialize GCP Service."""
        self.project_id = settings.VERTEX_AI_PROJECT_ID
        self.location = settings.VERTEX_AI_LOCATION or "us-central1"
        # Enable GCP if either AI features are enabled OR Google OAuth credentials are configured
        self.google_oauth_client_id = settings.GOOGLE_OAUTH_CLIENT_ID
        self.google_oauth_client_secret = settings.GOOGLE_OAUTH_CLIENT_SECRET
        self.has_google_oauth = bool(self.google_oauth_client_id and self.google_oauth_client_secret)
        self.enabled = (settings.ENABLE_AI_FEATURES or self.has_google_oauth) and GCP_AVAILABLE
        self.storage_client = None
        self.bucket_name = f"{self.project_id}-mathesis-sync" if self.project_id else None

        if self.enabled:
            self._initialize_gcp()
        else:
            logger.info("GCP features disabled. Configure Google OAuth credentials or set ENABLE_AI_FEATURES=True.")

    def _initialize_gcp(self):
        """Initialize GCP clients with proper authentication."""
        # Initialize Vertex AI
        aiplatform.init(project=self.project_id, location=self.location)

        # Initialize Cloud Storage
        self.storage_client = storage.Client(project=self.project_id)

        logger.info(f"GCP initialized successfully (project: {self.project_id}, location: {self.location})")

    def is_available(self) -> bool:
        """Check if GCP services are available and configured."""
        return self.enabled and self.storage_client is not None

    # ==================== Cloud Storage Operations ====================

    def upload_db_to_cloud(self, db_path: str, device_id: str) -> Optional[str]:
        """
        Upload SQLite database to Google Cloud Storage.

        Args:
            db_path: Local path to SQLite database file
            device_id: Device identifier for organization

        Returns:
            GCS URI (gs://bucket/path) or None if failed
        """
        if not self.is_available():
            logger.warning("GCP not available. Database backup skipped.")
            return None

        bucket = self.storage_client.bucket(self.bucket_name)
        timestamp = datetime.utcnow().isoformat()
        blob_name = f"backups/{device_id}/mathesis_lab_{timestamp}.db"
        blob = bucket.blob(blob_name)

        blob.upload_from_filename(db_path)
        gcs_uri = f"gs://{self.bucket_name}/{blob_name}"

        logger.info(f"✅ Database backed up to GCS: {gcs_uri}")
        return gcs_uri

    def download_db_from_cloud(self, device_id: str, output_path: str) -> bool:
        """
        Download latest SQLite database from Google Cloud Storage.

        Args:
            device_id: Device identifier
            output_path: Where to save the downloaded file

        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            logger.warning("GCP not available. Database download skipped.")
            return False

        bucket = self.storage_client.bucket(self.bucket_name)
        prefix = f"backups/{device_id}/"

        # List all backups for this device, sorted by creation time
        blobs = sorted(
            bucket.list_blobs(prefix=prefix),
            key=lambda b: b.time_created,
            reverse=True
        )

        if not blobs:
            logger.warning(f"No backups found for device {device_id}")
            return False

        # Download the most recent backup
        latest_blob = blobs[0]
        latest_blob.download_to_filename(output_path)

        logger.info(f"✅ Database downloaded from GCS: {latest_blob.name}")
        return True

    def list_backups(self, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all database backups in Cloud Storage.

        Args:
            device_id: Optional filter by device ID

        Returns:
            List of backup metadata
        """
        if not self.is_available():
            return []

        bucket = self.storage_client.bucket(self.bucket_name)
        prefix = f"backups/{device_id}/" if device_id else "backups/"

        backups = []
        for blob in bucket.list_blobs(prefix=prefix):
            backups.append({
                "name": blob.name,
                "size_bytes": blob.size,
                "created_at": blob.time_created.isoformat(),
                "device_id": blob.name.split("/")[1],
                "gcs_uri": f"gs://{self.bucket_name}/{blob.name}"
            })

        return sorted(backups, key=lambda x: x["created_at"], reverse=True)

    def delete_old_backups(self, device_id: str, keep_count: int = 5) -> int:
        """
        Delete old backups, keeping only the most recent ones.

        Args:
            device_id: Device identifier
            keep_count: Number of backups to keep

        Returns:
            Number of backups deleted
        """
        if not self.is_available():
            return 0

        bucket = self.storage_client.bucket(self.bucket_name)
        prefix = f"backups/{device_id}/"

        blobs = sorted(
            bucket.list_blobs(prefix=prefix),
            key=lambda b: b.time_created,
            reverse=True
        )

        deleted_count = 0
        for blob in blobs[keep_count:]:
            blob.delete()
            deleted_count += 1

        logger.info(f"🗑️  Deleted {deleted_count} old backups for device {device_id}")
        return deleted_count

    # ==================== Vertex AI Operations ====================

    def get_vertex_ai_info(self) -> Dict[str, Any]:
        """
        Get Vertex AI configuration and status information.

        Returns:
            Dictionary with Vertex AI configuration and Google Drive OAuth status
        """
        has_oauth = self.has_google_oauth
        is_available = self.is_available()

        return {
            "enabled": self.enabled,  # True if OAuth credentials are present
            "project_id": self.project_id,
            "location": self.location,
            "gcp_available": GCP_AVAILABLE,
            "has_google_oauth": has_oauth,
            "features": {
                "cloud_storage": is_available,
                "vertex_ai": is_available,
                "multi_device_sync": has_oauth,  # Enabled if OAuth credentials exist
                "backup_restore": is_available,
                "gemini": False  # Gemini explicitly disabled
            },
            "available_services": ["google_oauth"] if has_oauth else []
        }

    # ==================== Sync Helper Methods ====================

    def create_sync_metadata(
        self,
        device_id: str,
        device_name: str,
        drive_file_id: str,
        last_synced_timestamp: str
    ) -> Dict[str, Any]:
        """
        Create sync metadata for device synchronization.

        Args:
            device_id: Unique device identifier
            device_name: Human-readable device name
            drive_file_id: Google Drive file ID for mathesis_lab.db
            last_synced_timestamp: ISO 8601 timestamp

        Returns:
            Sync metadata dictionary
        """
        return {
            "device_id": device_id,
            "device_name": device_name,
            "drive_file_id": drive_file_id,
            "last_synced_drive_timestamp": last_synced_timestamp,
            "last_synced_local_timestamp": datetime.utcnow().isoformat(),
            "sync_status": "IDLE",
            "conflict_files": []
        }

    def get_backup_restoration_options(self, device_id: str) -> Dict[str, Any]:
        """
        Get available backup options for device restoration.

        Args:
            device_id: Device identifier

        Returns:
            Dictionary with restoration options
        """
        backups = self.list_backups(device_id)

        return {
            "available_backups": len(backups),
            "backups": backups,
            "device_id": device_id,
            "latest_backup": backups[0] if backups else None
        }

    def list_sync_devices(self) -> List[Dict[str, Any]]:
        """
        List all registered devices for multi-device synchronization.

        Fetches device sync metadata from Cloud Storage or database.
        Returns empty list if GCP is not available.

        Returns:
            List of device sync metadata dictionaries with keys:
            - device_id: Unique device identifier
            - device_name: Human-readable device name
            - drive_file_id: Google Drive file ID for mathesis_lab.db
            - last_synced_drive_timestamp: Last sync time with Drive
            - last_synced_local_timestamp: Last local sync time
            - sync_status: Current sync status (IDLE, SYNCING, ERROR)
            - conflict_files: List of conflicted files during sync
        """
        if not self.is_available():
            logger.debug("GCP not available. Returning empty devices list.")
            return []

        # TODO: Implement actual device list retrieval from:
        # 1. Cloud Storage metadata files
        # 2. Database sync_devices table (when implemented)
        # 3. Google Drive file properties
        #
        # For now, return empty list as device sync table not yet created.
        # This is a stub awaiting proper implementation.
        devices = []
        logger.info(f"Retrieved {len(devices)} registered sync devices from GCP")
        return devices


# Global GCP Service instance
gcp_service = GCPService()


def get_gcp_service() -> GCPService:
    """Get global GCP Service instance."""
    return gcp_service
