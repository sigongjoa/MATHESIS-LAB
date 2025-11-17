"""
Sync Service for bi-directional synchronization between local DB and Google Drive.

Manages synchronization of curriculum nodes between SQLite and Google Drive storage.
Handles conflict detection and resolution based on configurable strategies.
"""

from datetime import datetime, UTC, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from uuid import UUID
import json

from sqlalchemy.orm import Session

from backend.app.models.curriculum import Curriculum, Node
from backend.app.models.sync_metadata import SyncMetadata, CurriculumDriveFolder
from backend.app.services.google_drive_service import (
    GoogleDriveService,
    GoogleDriveServiceException,
)
from backend.app.core.config import settings


class ConflictResolutionStrategy(str, Enum):
    """Strategy for resolving conflicts between local and Drive versions"""
    LAST_WRITE_WINS = "last_write_wins"  # Use most recently modified version
    LOCAL_WINS = "local_wins"             # Always prefer local version
    DRIVE_WINS = "drive_wins"             # Always prefer Drive version


class SyncStatus(str, Enum):
    """Status of synchronization"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class SyncException(Exception):
    """Base exception for sync errors"""
    pass


class SyncConflictException(SyncException):
    """Exception raised when conflict cannot be resolved"""
    pass


class SyncService:
    """
    Service for managing bi-directional synchronization between local DB and Google Drive.

    Provides methods for:
    - Detecting changes in local DB and Drive
    - Resolving conflicts using configurable strategies
    - Syncing nodes up (local → Drive) and down (Drive → local)
    - Tracking sync history and metadata
    """

    def __init__(
        self,
        db: Session,
        google_drive_service: GoogleDriveService,
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS,
    ):
        """
        Initialize Sync Service.

        Args:
            db: SQLAlchemy database session
            google_drive_service: Google Drive API service instance
            conflict_strategy: How to resolve conflicts (default: LAST_WRITE_WINS)
        """
        self.db = db
        self.drive_service = google_drive_service
        self.conflict_strategy = conflict_strategy
        self.max_retries = settings.MAX_SYNC_RETRIES if hasattr(settings, 'MAX_SYNC_RETRIES') else 3

    async def sync_curriculum(
        self,
        curriculum_id: str,
        direction: str = "bidirectional",
    ) -> Dict[str, Any]:
        """
        Synchronize a curriculum between local DB and Google Drive.

        Args:
            curriculum_id: UUID of curriculum to sync
            direction: "up" (local→Drive), "down" (Drive→local), "bidirectional"

        Returns:
            Sync result with statistics (synced, updated, deleted, conflicts)

        Raises:
            SyncException: If sync fails
        """
        curriculum = self.db.query(Curriculum).filter(
            Curriculum.curriculum_id == curriculum_id
        ).first()

        if not curriculum:
            raise SyncException(f"Curriculum {curriculum_id} not found")

        # Get or create Drive folder mapping
        drive_folder = self.db.query(CurriculumDriveFolder).filter(
            CurriculumDriveFolder.curriculum_id == curriculum_id
        ).first()

        if not drive_folder:
            raise SyncException(f"No Drive folder mapping for curriculum {curriculum_id}")

        result = {
            "curriculum_id": curriculum_id,
            "synced_nodes": [],
            "updated_nodes": [],
            "deleted_nodes": [],
            "conflicts": [],
            "errors": [],
            "direction": direction,
            "timestamp": datetime.now(UTC),
        }

        try:
            if direction in ("up", "bidirectional"):
                await self._sync_up(curriculum_id, drive_folder.drive_folder_id, result)

            if direction in ("down", "bidirectional"):
                await self._sync_down(curriculum_id, drive_folder.drive_folder_id, result)

            # Mark sync as completed
            result["status"] = "completed"
            result["synced_count"] = len(result["synced_nodes"])
            result["updated_count"] = len(result["updated_nodes"])
            result["deleted_count"] = len(result["deleted_nodes"])
            result["conflict_count"] = len(result["conflicts"])

        except Exception as e:
            result["status"] = "failed"
            result["errors"].append(str(e))

        return result

    async def _sync_up(
        self,
        curriculum_id: str,
        drive_folder_id: str,
        result: Dict[str, Any],
    ) -> None:
        """
        Sync local changes up to Google Drive (local → Drive).

        Args:
            curriculum_id: UUID of curriculum
            drive_folder_id: Google Drive folder ID
            result: Result dictionary to populate
        """
        # Get all nodes in curriculum
        nodes = self.db.query(Node).filter(
            Node.curriculum_id == curriculum_id
        ).all()

        for node in nodes:
            sync_meta = self.db.query(SyncMetadata).filter(
                SyncMetadata.node_id == node.node_id
            ).first()

            if not sync_meta:
                # New node - create Drive file
                await self._create_node_on_drive(node, drive_folder_id, result)
            elif not sync_meta.is_synced:
                # Modified node - update Drive file
                await self._update_node_on_drive(node, sync_meta, result)

    async def _sync_down(
        self,
        curriculum_id: str,
        drive_folder_id: str,
        result: Dict[str, Any],
    ) -> None:
        """
        Sync changes down from Google Drive (Drive → local).

        Args:
            curriculum_id: UUID of curriculum
            drive_folder_id: Google Drive folder ID
            result: Result dictionary to populate
        """
        # Get all files in Drive folder
        drive_files = await self.drive_service.list_nodes_on_drive(drive_folder_id)

        local_files = set(
            self.db.query(SyncMetadata.google_drive_file_id)
            .filter(SyncMetadata.google_drive_file_id.isnot(None))
            .all()
        )

        for drive_file in drive_files:
            file_id = drive_file["id"]

            sync_meta = self.db.query(SyncMetadata).filter(
                SyncMetadata.google_drive_file_id == file_id
            ).first()

            if not sync_meta:
                # New file on Drive - create local node
                await self._create_node_locally(file_id, curriculum_id, result)
            else:
                # Existing file - check for updates
                await self._check_drive_updates(sync_meta, file_id, result)

        # Check for deleted files (in local but not on Drive)
        for file_id_tuple in local_files:
            file_id = file_id_tuple[0]
            if not any(f["id"] == file_id for f in drive_files):
                sync_meta = self.db.query(SyncMetadata).filter(
                    SyncMetadata.google_drive_file_id == file_id
                ).first()
                if sync_meta and sync_meta.node_id:
                    result["deleted_nodes"].append(sync_meta.node_id)
                    # Mark node as deleted locally
                    node = self.db.query(Node).filter(
                        Node.node_id == sync_meta.node_id
                    ).first()
                    if node:
                        self.db.delete(node)

    async def _create_node_on_drive(
        self,
        node: Node,
        drive_folder_id: str,
        result: Dict[str, Any],
    ) -> None:
        """Create a new node on Google Drive."""
        try:
            node_data = {
                "id": str(node.node_id),
                "title": node.title,
                "content": node.node_content.markdown_content if node.node_content else "",
                "children": [str(child.node_id) for child in node.children],
                "created_at": node.created_at.isoformat() if node.created_at else None,
                "modified_at": node.updated_at.isoformat() if node.updated_at else None,
            }

            file_id = await self.drive_service.save_node_to_drive(
                UUID(node.node_id),
                node_data,
                drive_folder_id,
            )

            # Create sync metadata
            sync_meta = SyncMetadata(
                curriculum_id=node.curriculum_id,
                node_id=node.node_id,
                google_drive_file_id=file_id,
                last_local_modified=node.updated_at,
                last_drive_modified=datetime.now(UTC),
                last_sync_time=datetime.now(UTC),
                is_synced=True,
            )
            self.db.add(sync_meta)
            self.db.commit()

            result["synced_nodes"].append(node.node_id)

        except Exception as e:
            result["errors"].append(f"Failed to create node {node.node_id}: {str(e)}")

    async def _update_node_on_drive(
        self,
        node: Node,
        sync_meta: SyncMetadata,
        result: Dict[str, Any],
    ) -> None:
        """Update an existing node on Google Drive."""
        try:
            node_data = {
                "id": str(node.node_id),
                "title": node.title,
                "content": node.node_content.markdown_content if node.node_content else "",
                "children": [str(child.node_id) for child in node.children],
                "created_at": node.created_at.isoformat() if node.created_at else None,
                "modified_at": node.updated_at.isoformat() if node.updated_at else None,
            }

            await self.drive_service.update_node_on_drive(
                sync_meta.google_drive_file_id,
                node_data,
            )

            # Update sync metadata
            sync_meta.last_local_modified = node.updated_at
            sync_meta.last_drive_modified = datetime.now(UTC)
            sync_meta.last_sync_time = datetime.now(UTC)
            sync_meta.is_synced = True
            self.db.commit()

            result["updated_nodes"].append(node.node_id)

        except Exception as e:
            result["errors"].append(f"Failed to update node {node.node_id}: {str(e)}")

    async def _create_node_locally(
        self,
        file_id: str,
        curriculum_id: str,
        result: Dict[str, Any],
    ) -> None:
        """Create a new node locally from Drive file."""
        try:
            node_data = await self.drive_service.load_node_from_drive(file_id)

            # Create node
            node = Node(
                node_id=node_data.get("id"),
                curriculum_id=curriculum_id,
                title=node_data.get("title", "Untitled"),
                order_index=0,
            )
            self.db.add(node)
            self.db.flush()

            # Create sync metadata
            sync_meta = SyncMetadata(
                curriculum_id=curriculum_id,
                node_id=node.node_id,
                google_drive_file_id=file_id,
                last_local_modified=datetime.now(UTC),
                last_drive_modified=datetime.fromisoformat(
                    node_data.get("modified_at", datetime.now(UTC).isoformat())
                ),
                last_sync_time=datetime.now(UTC),
                is_synced=True,
            )
            self.db.add(sync_meta)
            self.db.commit()

            result["synced_nodes"].append(node.node_id)

        except Exception as e:
            result["errors"].append(f"Failed to create local node from {file_id}: {str(e)}")

    async def _check_drive_updates(
        self,
        sync_meta: SyncMetadata,
        file_id: str,
        result: Dict[str, Any],
    ) -> None:
        """Check if Drive file has been updated and sync down if necessary."""
        try:
            # Get file metadata from Drive
            metadata = await self.drive_service.get_file_metadata(file_id)
            drive_modified = datetime.fromisoformat(metadata["modifiedTime"].replace("Z", "+00:00"))

            # Check if Drive version is newer
            if sync_meta.last_drive_modified and drive_modified > sync_meta.last_drive_modified:
                # Load updated data from Drive
                node_data = await self.drive_service.load_node_from_drive(file_id)

                # Get local node
                node = self.db.query(Node).filter(
                    Node.node_id == sync_meta.node_id
                ).first()

                if node:
                    # Resolve conflict if both have been modified since last sync
                    local_newer = (
                        sync_meta.last_local_modified and
                        sync_meta.last_local_modified > sync_meta.last_sync_time
                    )

                    if local_newer:
                        # Conflict detected
                        conflict = await self._resolve_conflict(
                            node,
                            node_data,
                            sync_meta,
                        )
                        result["conflicts"].append(conflict)
                    else:
                        # Update local node from Drive
                        node.title = node_data.get("title", node.title)
                        if node.node_content:
                            node.node_content.markdown_content = node_data.get("content", "")

                        sync_meta.last_drive_modified = drive_modified
                        sync_meta.last_sync_time = datetime.now(UTC)
                        sync_meta.is_synced = True
                        self.db.commit()

                        result["updated_nodes"].append(node.node_id)

        except Exception as e:
            result["errors"].append(f"Failed to check updates for {file_id}: {str(e)}")

    async def _resolve_conflict(
        self,
        local_node: Node,
        drive_data: Dict[str, Any],
        sync_meta: SyncMetadata,
    ) -> Dict[str, Any]:
        """
        Resolve conflict between local and Drive versions.

        Returns conflict information and applies resolution based on strategy.
        """
        conflict_info = {
            "node_id": local_node.node_id,
            "strategy_used": self.conflict_strategy.value,
            "local_version": {
                "title": local_node.title,
                "modified_at": local_node.updated_at.isoformat() if local_node.updated_at else None,
            },
            "drive_version": {
                "title": drive_data.get("title"),
                "modified_at": drive_data.get("modified_at"),
            },
        }

        if self.conflict_strategy == ConflictResolutionStrategy.LAST_WRITE_WINS:
            # Compare modification times
            local_mod = local_node.updated_at or datetime.now(UTC)
            drive_mod = datetime.fromisoformat(
                drive_data.get("modified_at", datetime.now(UTC).isoformat())
            )

            if drive_mod > local_mod:
                # Drive is newer - update local
                local_node.title = drive_data.get("title", local_node.title)
                conflict_info["resolution"] = "drive_version_applied"
            else:
                # Local is newer - keep local but update Drive
                conflict_info["resolution"] = "local_version_kept"

        elif self.conflict_strategy == ConflictResolutionStrategy.LOCAL_WINS:
            conflict_info["resolution"] = "local_version_kept"

        elif self.conflict_strategy == ConflictResolutionStrategy.DRIVE_WINS:
            local_node.title = drive_data.get("title", local_node.title)
            conflict_info["resolution"] = "drive_version_applied"

        sync_meta.last_sync_time = datetime.now(UTC)
        sync_meta.is_synced = True
        self.db.commit()

        return conflict_info

    def get_sync_status(self, curriculum_id: str) -> Dict[str, Any]:
        """Get current sync status for a curriculum."""
        sync_meta_list = self.db.query(SyncMetadata).filter(
            SyncMetadata.curriculum_id == curriculum_id
        ).all()

        synced_count = sum(1 for m in sync_meta_list if m.is_synced)
        pending_count = len(sync_meta_list) - synced_count

        latest_sync = max(
            (m.last_sync_time for m in sync_meta_list if m.last_sync_time),
            default=None,
        )

        return {
            "curriculum_id": curriculum_id,
            "total_nodes": len(sync_meta_list),
            "synced_nodes": synced_count,
            "pending_nodes": pending_count,
            "last_sync_time": latest_sync.isoformat() if latest_sync else None,
            "is_fully_synced": pending_count == 0,
        }


# Singleton instance
_sync_service_instance: Optional[SyncService] = None


def get_sync_service(
    db: Session,
    drive_service: GoogleDriveService,
) -> SyncService:
    """
    Get or create Sync Service instance.

    Args:
        db: SQLAlchemy database session
        drive_service: Google Drive service instance

    Returns:
        SyncService instance
    """
    global _sync_service_instance

    # Get conflict strategy from settings
    conflict_strategy = ConflictResolutionStrategy(
        getattr(settings, 'CONFLICT_RESOLUTION_MODE', 'last_write_wins')
    )

    if _sync_service_instance is None:
        _sync_service_instance = SyncService(db, drive_service, conflict_strategy)

    return _sync_service_instance
