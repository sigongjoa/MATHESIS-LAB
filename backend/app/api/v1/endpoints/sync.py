"""
Synchronization API Endpoints

REST API endpoints for managing synchronization between local DB and Google Drive.
Provides endpoints for manual sync, status checking, and sync control.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from backend.app.db.session import get_db
from backend.app.services.sync_service import (
    get_sync_service,
    SyncService,
    SyncException,
)

# Import sync scheduler and related services
from backend.app.services.sync_scheduler import (
    get_sync_scheduler,
    SyncScheduler,
)
SYNC_SCHEDULER_AVAILABLE = True

from backend.app.services.google_drive_service import get_google_drive_service

from backend.app.schemas.sync import (
    SyncStartRequest,
    SyncStartResponse,
    SyncStatusResponse,
    SyncHistoryResponse,
)

router = APIRouter(prefix="/sync", tags=["sync"])


def get_sync_dependencies(db: Session = Depends(get_db)):
    """Get sync service dependencies."""
    drive_service = get_google_drive_service()
    sync_service = get_sync_service(db, drive_service)
    sync_scheduler = get_sync_scheduler(db, sync_service)
    return sync_service, sync_scheduler


@router.post(
    "/start",
    response_model=SyncStartResponse,
    status_code=status.HTTP_200_OK,
    summary="Start manual synchronization",
    responses={
        200: {"description": "Sync started successfully"},
        400: {"description": "Invalid curriculum ID or sync already in progress"},
        404: {"description": "Curriculum not found"},
        500: {"description": "Sync failed"},
    }
)
async def start_sync(
    request: SyncStartRequest,
    deps=Depends(get_sync_dependencies),
    db: Session = Depends(get_db),
) -> SyncStartResponse:
    """
    Start manual synchronization of a curriculum.

    **Request Body:**
    - curriculum_id: UUID of curriculum to sync
    - direction: "up" (local→Drive), "down" (Drive→local), or "bidirectional"

    **Returns:**
    - sync_id: Unique identifier for this sync operation
    - curriculum_id: The curriculum being synced
    - status: Current sync status
    - started_at: Timestamp when sync started

    **Usage:**
    1. Call this endpoint to start manual sync
    2. Poll /api/v1/sync/status to monitor progress
    3. Or wait for completion and check /api/v1/sync/history
    """
    sync_service, sync_scheduler = deps

    # Start sync immediately
    result = await sync_service.sync_curriculum(
        request.curriculum_id,
        direction=request.direction,
    )

    return SyncStartResponse(
        curriculum_id=request.curriculum_id,
        status=result.get("status", "pending"),
        synced_count=result.get("synced_count", 0),
        updated_count=result.get("updated_count", 0),
        deleted_count=result.get("deleted_count", 0),
        conflict_count=result.get("conflict_count", 0),
        direction=request.direction,
    )


@router.get(
    "/status",
    response_model=SyncStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sync status",
    responses={
        200: {"description": "Sync status retrieved"},
        404: {"description": "Curriculum not found"},
        500: {"description": "Failed to get status"},
    }
)
async def get_status(
    curriculum_id: str,
    deps=Depends(get_sync_dependencies),
) -> SyncStatusResponse:
    """
    Get current synchronization status for a curriculum.

    **Query Parameters:**
    - curriculum_id: UUID of curriculum

    **Returns:**
    - curriculum_id: The curriculum ID
    - total_nodes: Total nodes in curriculum
    - synced_nodes: Number of synced nodes
    - pending_nodes: Number of pending nodes
    - last_sync_time: When last sync completed
    - is_fully_synced: Whether all nodes are synced
    - active_sync: Currently active sync operation (if any)

    **Usage:**
    Poll this endpoint while sync is in progress to monitor status.
    """
    sync_service, sync_scheduler = deps

    status_info = sync_service.get_sync_status(curriculum_id)

    return SyncStatusResponse(
        curriculum_id=curriculum_id,
        total_nodes=status_info.get("total_nodes", 0),
        synced_nodes=status_info.get("synced_nodes", 0),
        pending_nodes=status_info.get("pending_nodes", 0),
        last_sync_time=status_info.get("last_sync_time"),
        is_fully_synced=status_info.get("is_fully_synced", False),
    )


@router.get(
    "/history",
    response_model=SyncHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get sync history",
    responses={
        200: {"description": "Sync history retrieved"},
        404: {"description": "Curriculum not found"},
        500: {"description": "Failed to get history"},
    }
)
async def get_history(
    curriculum_id: str,
    limit: int = 10,
    deps=Depends(get_sync_dependencies),
) -> SyncHistoryResponse:
    """
    Get synchronization history for a curriculum.

    **Query Parameters:**
    - curriculum_id: UUID of curriculum
    - limit: Maximum number of history entries (default: 10)

    **Returns:**
    - curriculum_id: The curriculum ID
    - entries: List of sync history entries with timestamps and statistics
    - total_entries: Total number of history entries available

    **Usage:**
    View past sync operations and their results.
    """
    sync_service, sync_scheduler = deps

    history = sync_scheduler.get_sync_history(curriculum_id, limit)

    return SyncHistoryResponse(
        curriculum_id=curriculum_id,
        entries=history,
        total_entries=len(history),
    )


@router.post(
    "/pause",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Pause synchronization",
    responses={
        204: {"description": "Sync paused successfully"},
        404: {"description": "Curriculum not found or sync not in progress"},
        500: {"description": "Failed to pause sync"},
    }
)
async def pause_sync(
    curriculum_id: str,
    deps=Depends(get_sync_dependencies),
) -> None:
    """
    Pause synchronization for a curriculum.

    **Query Parameters:**
    - curriculum_id: UUID of curriculum

    **Usage:**
    Temporarily halt sync operations without canceling them.
    """
    sync_service, sync_scheduler = deps

    sync_scheduler.pause_sync(curriculum_id)


@router.post(
    "/resume",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Resume synchronization",
    responses={
        204: {"description": "Sync resumed successfully"},
        404: {"description": "Curriculum not found or sync not paused"},
        500: {"description": "Failed to resume sync"},
    }
)
async def resume_sync(
    curriculum_id: str,
    deps=Depends(get_sync_dependencies),
) -> None:
    """
    Resume synchronization for a paused curriculum.

    **Query Parameters:**
    - curriculum_id: UUID of curriculum

    **Usage:**
    Resume sync operations that were previously paused.
    """
    sync_service, sync_scheduler = deps

    sync_scheduler.resume_sync(curriculum_id)


@router.get(
    "/all-status",
    status_code=status.HTTP_200_OK,
    summary="Get sync status for all curriculums",
    responses={
        200: {"description": "All sync statuses retrieved"},
        500: {"description": "Failed to get status"},
    }
)
async def get_all_status(
    deps=Depends(get_sync_dependencies),
) -> dict:
    """
    Get synchronization status for all curriculums.

    **Returns:**
    - total_curriculums: Total number of curriculums
    - active_syncs: Number of currently syncing curriculums
    - curriculums: Dictionary of sync status for each curriculum

    **Usage:**
    Get overview of sync status across entire system.
    """
    sync_service, sync_scheduler = deps

    return sync_scheduler.get_all_sync_status()
