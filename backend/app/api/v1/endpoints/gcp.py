"""
GCP Integration API Endpoints

Provides REST endpoints for:
- Database backup and restoration
- Cloud storage operations
- Device sync metadata management
- Vertex AI information
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import os
from pathlib import Path

from backend.app.services.gcp_service import get_gcp_service, GCPService
from backend.app.core.config import settings

router = APIRouter(prefix="/gcp", tags=["gcp"])


# ==================== Request/Response Models ====================

class SyncMetadataRequest(BaseModel):
    """Request model for creating sync metadata."""
    device_id: str
    device_name: str
    drive_file_id: str
    last_synced_timestamp: str


class BackupInfo(BaseModel):
    """Information about a database backup."""
    name: str
    size_bytes: int
    created_at: str
    device_id: str
    gcs_uri: str


class FeaturesAvailable(BaseModel):
    """Available GCP features."""
    cloud_storage: bool
    backup_restore: bool
    multi_device_sync: bool
    ai_features: bool


class GCPStatus(BaseModel):
    """GCP configuration and status."""
    enabled: bool
    project_id: Optional[str]
    location: str
    features_available: FeaturesAvailable
    available_services: List[str] = []
    last_health_check: str = ""


# ==================== Database Backup & Restoration ====================

def _get_database_path() -> str:
    """Extract database file path from SQLite DATABASE_URL."""
    db_url = settings.DATABASE_URL
    # SQLite URL format: sqlite:///path/to/db.db
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "")
    elif db_url.startswith("sqlite://"):
        return db_url.replace("sqlite://", "")
    else:
        # Fallback for relative paths
        return "mathesis_lab.db"


@router.post("/backup")
async def backup_database(
    device_id: str,
    gcp_service: GCPService = Depends(get_gcp_service)
) -> Dict[str, Any]:
    """
    Backup SQLite database to Google Cloud Storage.

    Args:
        device_id: Device identifier for organizing backups

    Returns:
        Backup result with GCS URI

    Raises:
        HTTPException: If GCP not available or backup fails
    """
    if not gcp_service.is_available():
        raise HTTPException(status_code=503, detail="GCP service not available")

    db_path = _get_database_path()

    # Verify database file exists
    if not Path(db_path).exists():
        raise HTTPException(
            status_code=400,
            detail=f"Database file not found at {db_path}"
        )

    gcs_uri = gcp_service.upload_db_to_cloud(db_path, device_id)

    if not gcs_uri:
        raise HTTPException(status_code=500, detail="Failed to backup database")

    return {
        "status": "success",
        "message": f"Database backed up to {gcs_uri}",
        "gcs_uri": gcs_uri,
        "device_id": device_id
    }


@router.post("/restore")
async def restore_database(
    device_id: str,
    output_path: str = "mathesis_lab_restored.db",
    gcp_service: GCPService = Depends(get_gcp_service)
) -> Dict[str, Any]:
    """
    Restore SQLite database from Google Cloud Storage.

    Args:
        device_id: Device identifier
        output_path: Where to save the restored database

    Returns:
        Restoration result

    Raises:
        HTTPException: If GCP not available or restore fails
    """
    if not gcp_service.is_available():
        raise HTTPException(status_code=503, detail="GCP service not available")

    success = gcp_service.download_db_from_cloud(device_id, output_path)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to restore database")

    return {
        "status": "success",
        "message": "Database restored successfully",
        "output_path": output_path,
        "device_id": device_id
    }


# ==================== Backup Management ====================

@router.get("/backups", response_model=List[BackupInfo])
async def list_backups(
    device_id: Optional[str] = None,
    gcp_service: GCPService = Depends(get_gcp_service)
) -> List[BackupInfo]:
    """
    List all database backups in Cloud Storage.

    Args:
        device_id: Optional filter by specific device

    Returns:
        List of backup information sorted by creation date (newest first)
    """
    if not gcp_service.is_available():
        raise HTTPException(status_code=503, detail="GCP service not available")

    backups = gcp_service.list_backups(device_id)
    return [BackupInfo(**backup) for backup in backups]


@router.post("/backups/cleanup")
async def cleanup_old_backups(
    device_id: str,
    keep_count: int = 5,
    gcp_service: GCPService = Depends(get_gcp_service)
) -> Dict[str, Any]:
    """
    Delete old backups, keeping only the most recent ones.

    Args:
        device_id: Device identifier
        keep_count: Number of recent backups to keep (default: 5)

    Returns:
        Cleanup result with count of deleted backups

    Raises:
        HTTPException: If GCP not available
    """
    if not gcp_service.is_available():
        raise HTTPException(status_code=503, detail="GCP service not available")

    deleted_count = gcp_service.delete_old_backups(device_id, keep_count)

    return {
        "status": "success",
        "deleted_count": deleted_count,
        "kept_count": keep_count,
        "device_id": device_id,
        "message": f"Deleted {deleted_count} old backups, kept {keep_count} recent ones"
    }


# ==================== Device Sync Metadata ====================

@router.post("/sync-metadata")
async def create_sync_metadata(
    request: SyncMetadataRequest,
    gcp_service: GCPService = Depends(get_gcp_service)
) -> Dict[str, Any]:
    """
    Create sync metadata for multi-device synchronization.

    Args:
        request: Sync metadata request with device and Drive info

    Returns:
        Created sync metadata

    Raises:
        HTTPException: If GCP not available
    """
    if not gcp_service.is_available():
        raise HTTPException(status_code=503, detail="GCP service not available")

    metadata = gcp_service.create_sync_metadata(
        device_id=request.device_id,
        device_name=request.device_name,
        drive_file_id=request.drive_file_id,
        last_synced_timestamp=request.last_synced_timestamp
    )

    return {
        "status": "success",
        "metadata": metadata
    }


@router.get("/sync-devices")
async def list_sync_devices(
    gcp_service: GCPService = Depends(get_gcp_service)
) -> Dict[str, Any]:
    """
    List all registered devices for multi-device synchronization.

    Returns:
        List of registered devices with their sync metadata

    Raises:
        HTTPException: If GCP not available
    """
    if not gcp_service.is_available():
        # Return empty devices list if GCP not available
        return {"devices": []}

    devices = gcp_service.list_sync_devices()
    return {"devices": devices}


@router.get("/restoration-options/{device_id}")
async def get_restoration_options(
    device_id: str,
    gcp_service: GCPService = Depends(get_gcp_service)
) -> Dict[str, Any]:
    """
    Get available backup options for device restoration.

    Args:
        device_id: Device identifier

    Returns:
        Available restoration options and backups

    Raises:
        HTTPException: If GCP not available
    """
    if not gcp_service.is_available():
        raise HTTPException(status_code=503, detail="GCP service not available")

    options = gcp_service.get_backup_restoration_options(device_id)
    return options


# ==================== Status & Information ====================

@router.get("/status", response_model=GCPStatus)
async def get_gcp_status(
    gcp_service: GCPService = Depends(get_gcp_service)
) -> GCPStatus:
    """
    Get GCP configuration and service status.

    Returns:
        GCP status and feature availability
    """
    from datetime import datetime

    info = gcp_service.get_vertex_ai_info()
    return GCPStatus(
        enabled=info.get('enabled', False),
        project_id=info.get('project_id'),
        location=info.get('location', 'us-central1'),
        features_available=FeaturesAvailable(
            cloud_storage=info.get('features', {}).get('cloud_storage', False),
            backup_restore=info.get('features', {}).get('backup_restore', False),
            multi_device_sync=info.get('features', {}).get('multi_device_sync', False),
            ai_features=info.get('features', {}).get('ai_features', False),
        ),
        available_services=info.get('available_services', []),
        last_health_check=info.get('last_health_check', datetime.utcnow().isoformat())
    )


@router.get("/health")
async def health_check(
    gcp_service: GCPService = Depends(get_gcp_service)
) -> Dict[str, Any]:
    """
    Health check for GCP services.

    Returns:
        Health status of GCP integration
    """
    return {
        "status": "healthy" if gcp_service.is_available() else "degraded",
        "gcp_available": gcp_service.is_available(),
        "project_id": gcp_service.project_id,
        "message": "GCP services operational" if gcp_service.is_available() else "GCP services not configured"
    }
