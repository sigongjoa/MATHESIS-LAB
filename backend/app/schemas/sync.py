"""
Schemas for Synchronization API

Request and response models for sync endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SyncStartRequest(BaseModel):
    """Request to start synchronization"""
    curriculum_id: str = Field(..., description="UUID of curriculum to sync")
    direction: str = Field(
        default="bidirectional",
        description="Sync direction: 'up', 'down', or 'bidirectional'"
    )

    class Config:
        example = {
            "curriculum_id": "550e8400-e29b-41d4-a716-446655440000",
            "direction": "bidirectional"
        }


class SyncStartResponse(BaseModel):
    """Response from starting synchronization"""
    curriculum_id: str = Field(..., description="UUID of curriculum")
    status: str = Field(..., description="Sync status (pending, in_progress, completed, failed)")
    synced_count: int = Field(0, description="Number of nodes synced")
    updated_count: int = Field(0, description="Number of nodes updated")
    deleted_count: int = Field(0, description="Number of nodes deleted")
    conflict_count: int = Field(0, description="Number of conflicts encountered")
    direction: str = Field(..., description="Sync direction")

    class Config:
        example = {
            "curriculum_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "completed",
            "synced_count": 5,
            "updated_count": 2,
            "deleted_count": 0,
            "conflict_count": 1,
            "direction": "bidirectional"
        }


class SyncStatusResponse(BaseModel):
    """Response with synchronization status"""
    curriculum_id: str = Field(..., description="UUID of curriculum")
    total_nodes: int = Field(0, description="Total nodes in curriculum")
    synced_nodes: int = Field(0, description="Number of synced nodes")
    pending_nodes: int = Field(0, description="Number of pending nodes")
    last_sync_time: Optional[str] = Field(None, description="Timestamp of last sync")
    is_fully_synced: bool = Field(False, description="Whether all nodes are synced")

    class Config:
        example = {
            "curriculum_id": "550e8400-e29b-41d4-a716-446655440000",
            "total_nodes": 10,
            "synced_nodes": 8,
            "pending_nodes": 2,
            "last_sync_time": "2025-11-17T04:30:00+00:00",
            "is_fully_synced": False
        }


class SyncHistoryEntry(BaseModel):
    """Single sync history entry"""
    timestamp: str = Field(..., description="When the sync occurred")
    status: str = Field(..., description="Sync status (completed, failed)")
    synced_count: int = Field(0, description="Number of nodes synced")
    updated_count: int = Field(0, description="Number of nodes updated")
    conflict_count: int = Field(0, description="Number of conflicts")
    error_count: int = Field(0, description="Number of errors")

    class Config:
        example = {
            "timestamp": "2025-11-17T04:30:00+00:00",
            "status": "completed",
            "synced_count": 5,
            "updated_count": 2,
            "conflict_count": 0,
            "error_count": 0
        }


class SyncHistoryResponse(BaseModel):
    """Response with synchronization history"""
    curriculum_id: str = Field(..., description="UUID of curriculum")
    entries: List[SyncHistoryEntry] = Field([], description="List of sync history entries")
    total_entries: int = Field(0, description="Total number of history entries")

    class Config:
        example = {
            "curriculum_id": "550e8400-e29b-41d4-a716-446655440000",
            "entries": [
                {
                    "timestamp": "2025-11-17T04:30:00+00:00",
                    "status": "completed",
                    "synced_count": 5,
                    "updated_count": 2,
                    "conflict_count": 0,
                    "error_count": 0
                }
            ],
            "total_entries": 1
        }


class SyncConflictInfo(BaseModel):
    """Information about a sync conflict"""
    node_id: str = Field(..., description="UUID of node with conflict")
    strategy_used: str = Field(..., description="Conflict resolution strategy applied")
    local_version: Dict[str, Any] = Field(..., description="Local version info")
    drive_version: Dict[str, Any] = Field(..., description="Drive version info")
    resolution: str = Field(..., description="How the conflict was resolved")

    class Config:
        example = {
            "node_id": "550e8400-e29b-41d4-a716-446655440001",
            "strategy_used": "last_write_wins",
            "local_version": {
                "title": "Local Title",
                "modified_at": "2025-11-17T04:00:00+00:00"
            },
            "drive_version": {
                "title": "Drive Title",
                "modified_at": "2025-11-17T03:00:00+00:00"
            },
            "resolution": "local_version_kept"
        }
