"""
Unit tests for Sync Service

Tests synchronization logic, conflict resolution, and sync state management.
"""

import pytest
from datetime import datetime, UTC, timedelta
from uuid import UUID
from unittest.mock import Mock, AsyncMock, patch

from backend.app.services.sync_service import (
    SyncService,
    ConflictResolutionStrategy,
    SyncException,
)
from backend.app.models.curriculum import Curriculum, Node
from backend.app.models.sync_metadata import SyncMetadata, CurriculumDriveFolder


@pytest.fixture
def mock_db():
    """Create mock database session"""
    return Mock()


@pytest.fixture
def mock_drive_service():
    """Create mock Google Drive service"""
    service = Mock()
    service.save_node_to_drive = AsyncMock()
    service.load_node_from_drive = AsyncMock()
    service.update_node_on_drive = AsyncMock()
    service.delete_node_from_drive = AsyncMock()
    service.list_nodes_on_drive = AsyncMock()
    service.get_file_metadata = AsyncMock()
    return service


@pytest.fixture
def sync_service(mock_db, mock_drive_service):
    """Create SyncService instance"""
    return SyncService(
        db=mock_db,
        google_drive_service=mock_drive_service,
        conflict_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS,
    )


class TestSyncServiceInitialization:
    """Test SyncService initialization"""

    def test_sync_service_creates_successfully(self, sync_service):
        """Test that SyncService initializes correctly"""
        assert sync_service is not None
        assert sync_service.conflict_strategy == ConflictResolutionStrategy.LAST_WRITE_WINS
        assert sync_service.max_retries == 3

    def test_sync_service_with_local_wins_strategy(self, mock_db, mock_drive_service):
        """Test SyncService with LOCAL_WINS strategy"""
        service = SyncService(
            db=mock_db,
            google_drive_service=mock_drive_service,
            conflict_strategy=ConflictResolutionStrategy.LOCAL_WINS,
        )
        assert service.conflict_strategy == ConflictResolutionStrategy.LOCAL_WINS

    def test_sync_service_with_drive_wins_strategy(self, mock_db, mock_drive_service):
        """Test SyncService with DRIVE_WINS strategy"""
        service = SyncService(
            db=mock_db,
            google_drive_service=mock_drive_service,
            conflict_strategy=ConflictResolutionStrategy.DRIVE_WINS,
        )
        assert service.conflict_strategy == ConflictResolutionStrategy.DRIVE_WINS


class TestSyncUpOperation:
    """Test sync up (local → Drive) operations"""

    @pytest.mark.asyncio
    async def test_sync_up_modified_node(self, sync_service, mock_db, mock_drive_service):
        """Test syncing a modified node up to Drive"""
        curriculum_id = "550e8400-e29b-41d4-a716-446655440000"
        folder_id = "drive-folder-123"

        # Create mock node
        node = Mock(spec=Node)
        node.node_id = "node-123"
        node.curriculum_id = curriculum_id
        node.title = "Updated Node"
        node.updated_at = datetime.now(UTC)
        node.node_content = Mock()
        node.node_content.markdown_content = "# Updated"
        node.children = []

        # Create mock sync metadata (not synced)
        sync_meta = Mock(spec=SyncMetadata)
        sync_meta.node_id = "node-123"
        sync_meta.google_drive_file_id = "drive-file-123"
        sync_meta.is_synced = False
        sync_meta.last_local_modified = datetime.now(UTC)
        sync_meta.last_drive_modified = datetime.now(UTC)
        sync_meta.last_sync_time = datetime.now(UTC)

        # Mock database queries
        mock_query_nodes = Mock()
        mock_query_nodes.all.return_value = [node]
        mock_query_sync = Mock()
        mock_query_sync.first.return_value = sync_meta

        def mock_db_query(model):
            if model == Node:
                return Mock(filter=Mock(return_value=mock_query_nodes))
            elif model == SyncMetadata:
                return Mock(filter=Mock(return_value=mock_query_sync))
            return Mock()

        mock_db.query = mock_db_query

        # Mock Drive service
        mock_drive_service.update_node_on_drive = AsyncMock()

        # Run sync up
        result = {
            "synced_nodes": [],
            "updated_nodes": [],
            "deleted_nodes": [],
            "conflicts": [],
            "errors": [],
        }
        await sync_service._sync_up(curriculum_id, folder_id, result)

        # Verify update was called
        mock_drive_service.update_node_on_drive.assert_called_once()


class TestSyncDownOperation:
    """Test sync down (Drive → local) operations"""

    @pytest.mark.asyncio
    async def test_sync_down_new_file(self, sync_service, mock_db, mock_drive_service):
        """Test syncing a new file from Drive"""
        curriculum_id = "550e8400-e29b-41d4-a716-446655440000"
        folder_id = "drive-folder-123"

        # Mock Drive files
        drive_files = [
            {
                "id": "drive-file-123",
                "name": "node_550e8400-e29b-41d4-a716-446655440001.json",
                "modifiedTime": datetime.now(UTC).isoformat(),
            }
        ]

        # Mock database queries
        mock_db.query(SyncMetadata).filter().all.return_value = []  # No local files
        mock_db.query(SyncMetadata).filter().first.return_value = None  # New file

        # Mock Drive service
        mock_drive_service.list_nodes_on_drive.return_value = drive_files
        mock_drive_service.load_node_from_drive.return_value = {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "title": "New Node from Drive",
            "content": "# New Content",
            "modified_at": datetime.now(UTC).isoformat(),
        }

        # Run sync down
        result = {
            "synced_nodes": [],
            "updated_nodes": [],
            "deleted_nodes": [],
            "conflicts": [],
            "errors": [],
        }
        await sync_service._sync_down(curriculum_id, folder_id, result)

        # Verify load was called
        mock_drive_service.load_node_from_drive.assert_called_once_with("drive-file-123")


class TestConflictResolution:
    """Test conflict resolution strategies"""

    @pytest.mark.asyncio
    async def test_last_write_wins_local_newer(self, sync_service, mock_db):
        """Test LAST_WRITE_WINS strategy when local is newer"""
        node = Mock(spec=Node)
        node.node_id = "node-123"
        node.title = "Local Title"
        node.updated_at = datetime.now(UTC)

        sync_meta = Mock(spec=SyncMetadata)
        sync_meta.node_id = "node-123"
        sync_meta.last_local_modified = datetime.now(UTC) + timedelta(hours=1)
        sync_meta.last_sync_time = datetime.now(UTC)

        drive_data = {
            "title": "Drive Title",
            "modified_at": (datetime.now(UTC) - timedelta(hours=1)).isoformat(),
        }

        conflict = await sync_service._resolve_conflict(node, drive_data, sync_meta)

        assert conflict["strategy_used"] == "last_write_wins"
        assert conflict["resolution"] == "local_version_kept"

    @pytest.mark.asyncio
    async def test_last_write_wins_drive_newer(self, sync_service, mock_db):
        """Test LAST_WRITE_WINS strategy when Drive is newer"""
        node = Mock(spec=Node)
        node.node_id = "node-123"
        node.title = "Local Title"
        node.updated_at = datetime.now(UTC) - timedelta(hours=1)

        sync_meta = Mock(spec=SyncMetadata)
        sync_meta.node_id = "node-123"

        drive_data = {
            "title": "Drive Title",
            "modified_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
        }

        conflict = await sync_service._resolve_conflict(node, drive_data, sync_meta)

        assert conflict["strategy_used"] == "last_write_wins"
        assert conflict["resolution"] == "drive_version_applied"

    @pytest.mark.asyncio
    async def test_local_wins_strategy(self, mock_db, mock_drive_service):
        """Test LOCAL_WINS conflict resolution strategy"""
        sync_service = SyncService(
            db=mock_db,
            google_drive_service=mock_drive_service,
            conflict_strategy=ConflictResolutionStrategy.LOCAL_WINS,
        )

        node = Mock(spec=Node)
        sync_meta = Mock(spec=SyncMetadata)
        drive_data = {"title": "Drive Title"}

        conflict = await sync_service._resolve_conflict(node, drive_data, sync_meta)

        assert conflict["strategy_used"] == "local_wins"
        assert conflict["resolution"] == "local_version_kept"

    @pytest.mark.asyncio
    async def test_drive_wins_strategy(self, mock_db, mock_drive_service):
        """Test DRIVE_WINS conflict resolution strategy"""
        sync_service = SyncService(
            db=mock_db,
            google_drive_service=mock_drive_service,
            conflict_strategy=ConflictResolutionStrategy.DRIVE_WINS,
        )

        node = Mock(spec=Node)
        sync_meta = Mock(spec=SyncMetadata)
        drive_data = {"title": "Drive Title"}

        conflict = await sync_service._resolve_conflict(node, drive_data, sync_meta)

        assert conflict["strategy_used"] == "drive_wins"
        assert conflict["resolution"] == "drive_version_applied"


class TestSyncStatus:
    """Test sync status tracking"""

    def test_get_sync_status_all_synced(self, sync_service, mock_db):
        """Test getting sync status when all nodes are synced"""
        curriculum_id = "550e8400-e29b-41d4-a716-446655440000"

        # Create mock sync metadata
        sync_meta = Mock(spec=SyncMetadata)
        sync_meta.is_synced = True
        sync_meta.last_sync_time = datetime.now(UTC)

        mock_db.query(SyncMetadata).filter().all.return_value = [sync_meta]

        status = sync_service.get_sync_status(curriculum_id)

        assert status["curriculum_id"] == curriculum_id
        assert status["synced_nodes"] == 1
        assert status["pending_nodes"] == 0
        assert status["is_fully_synced"] is True

    def test_get_sync_status_pending_nodes(self, sync_service, mock_db):
        """Test getting sync status with pending nodes"""
        curriculum_id = "550e8400-e29b-41d4-a716-446655440000"

        # Create mock sync metadata (mixed)
        synced = Mock(spec=SyncMetadata)
        synced.is_synced = True
        synced.last_sync_time = datetime.now(UTC)

        pending = Mock(spec=SyncMetadata)
        pending.is_synced = False
        pending.last_sync_time = None

        mock_db.query(SyncMetadata).filter().all.return_value = [synced, pending]

        status = sync_service.get_sync_status(curriculum_id)

        assert status["total_nodes"] == 2
        assert status["synced_nodes"] == 1
        assert status["pending_nodes"] == 1
        assert status["is_fully_synced"] is False


class TestSyncExceptions:
    """Test exception handling"""

    @pytest.mark.asyncio
    async def test_sync_curriculum_not_found(self, sync_service, mock_db):
        """Test sync when curriculum doesn't exist"""
        curriculum_id = "550e8400-e29b-41d4-a716-446655440000"

        # Create mock query chain that returns None
        curriculum_query = Mock()
        curriculum_query.filter.return_value = Mock(first=Mock(return_value=None))

        def mock_db_query(model):
            if model == Curriculum:
                return curriculum_query
            return Mock()

        mock_db.query = mock_db_query

        with pytest.raises(SyncException, match="not found"):
            await sync_service.sync_curriculum(curriculum_id)

    @pytest.mark.asyncio
    async def test_sync_no_drive_folder(self, sync_service, mock_db):
        """Test sync when no Drive folder mapping exists"""
        curriculum_id = "550e8400-e29b-41d4-a716-446655440000"

        curriculum = Mock(spec=Curriculum)

        # Create mock query chains for different models
        curriculum_query = Mock()
        curriculum_query.filter.return_value = Mock(first=Mock(return_value=curriculum))

        drive_folder_query = Mock()
        drive_folder_query.filter.return_value = Mock(first=Mock(return_value=None))  # No Drive folder

        def mock_db_query(model):
            if model == Curriculum:
                return curriculum_query
            elif model == CurriculumDriveFolder:
                return drive_folder_query
            return Mock()

        mock_db.query = mock_db_query

        with pytest.raises(SyncException, match="No Drive folder mapping"):
            await sync_service.sync_curriculum(curriculum_id)
