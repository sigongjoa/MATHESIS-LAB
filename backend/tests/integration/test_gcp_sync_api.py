"""
Integration tests for GCP Sync API endpoints

Tests the full stack of GCP integration:
- Database backup and restore operations
- Sync metadata management
- Backup listing and cleanup
- Restoration options retrieval
- Status and health checks
"""

import json
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.services.gcp_service import GCPService, get_gcp_service


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_gcp_service():
    """Mock GCP service for testing."""
    service = MagicMock(spec=GCPService)
    service.is_available.return_value = True
    service.project_id = 'test-project'
    service.location = 'us-central1'

    def override_get_gcp_service():
        return service

    app.dependency_overrides[get_gcp_service] = override_get_gcp_service

    yield service

    app.dependency_overrides.clear()


class TestGCPBackupRestore:
    """Tests for database backup and restore operations."""

    def test_backup_database_success(self, client, mock_gcp_service):
        """Test successful database backup."""
        mock_gcp_service.upload_db_to_cloud.return_value = 'gs://bucket/backup.db'

        response = client.post('/api/v1/gcp/backup?device_id=test-device')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['device_id'] == 'test-device'
        assert 'gcs_uri' in data
        mock_gcp_service.upload_db_to_cloud.assert_called_once()

    def test_backup_database_gcp_unavailable(self, client, mock_gcp_service):
        """Test backup when GCP is unavailable."""
        mock_gcp_service.is_available.return_value = False

        response = client.post('/api/v1/gcp/backup?device_id=test-device')

        assert response.status_code == 503
        data = response.json()
        assert 'GCP service not available' in data['detail']

    def test_backup_database_failure(self, client, mock_gcp_service):
        """Test backup failure."""
        mock_gcp_service.upload_db_to_cloud.return_value = None

        response = client.post('/api/v1/gcp/backup?device_id=test-device')

        assert response.status_code == 500
        data = response.json()
        assert 'Failed to backup database' in data['detail']

    def test_restore_database_success(self, client, mock_gcp_service):
        """Test successful database restore."""
        mock_gcp_service.download_db_from_cloud.return_value = True

        response = client.post(
            '/api/v1/gcp/restore?device_id=test-device&output_path=mathesis_lab.db'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['device_id'] == 'test-device'
        mock_gcp_service.download_db_from_cloud.assert_called_once()

    def test_restore_database_gcp_unavailable(self, client, mock_gcp_service):
        """Test restore when GCP is unavailable."""
        mock_gcp_service.is_available.return_value = False

        response = client.post(
            '/api/v1/gcp/restore?device_id=test-device&output_path=mathesis_lab.db'
        )

        assert response.status_code == 503

    def test_restore_database_failure(self, client, mock_gcp_service):
        """Test restore failure."""
        mock_gcp_service.download_db_from_cloud.return_value = False

        response = client.post(
            '/api/v1/gcp/restore?device_id=test-device&output_path=mathesis_lab.db'
        )

        assert response.status_code == 500


class TestGCPBackupManagement:
    """Tests for backup management operations."""

    def test_list_backups_success(self, client, mock_gcp_service):
        """Test listing backups."""
        mock_backups = [
            {
                'name': 'backup1.db',
                'size_bytes': 1024,
                'created_at': '2024-01-15T10:00:00Z',
                'device_id': 'test-device',
                'gcs_uri': 'gs://bucket/backup1.db'
            },
            {
                'name': 'backup2.db',
                'size_bytes': 2048,
                'created_at': '2024-01-14T10:00:00Z',
                'device_id': 'test-device',
                'gcs_uri': 'gs://bucket/backup2.db'
            }
        ]
        mock_gcp_service.list_backups.return_value = mock_backups

        response = client.get('/api/v1/gcp/backups?device_id=test-device')

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]['name'] == 'backup1.db'
        mock_gcp_service.list_backups.assert_called_once_with('test-device')

    def test_list_backups_no_filter(self, client, mock_gcp_service):
        """Test listing all backups without device filter."""
        mock_gcp_service.list_backups.return_value = []

        response = client.get('/api/v1/gcp/backups')

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        mock_gcp_service.list_backups.assert_called_once_with(None)

    def test_cleanup_old_backups_success(self, client, mock_gcp_service):
        """Test cleanup of old backups."""
        mock_gcp_service.delete_old_backups.return_value = 5

        response = client.post(
            '/api/v1/gcp/backups/cleanup?device_id=test-device&keep_count=3'
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['deleted_count'] == 5
        assert data['kept_count'] == 3
        mock_gcp_service.delete_old_backups.assert_called_once_with(
            'test-device', 3
        )

    def test_cleanup_with_default_keep_count(self, client, mock_gcp_service):
        """Test cleanup with default keep_count."""
        mock_gcp_service.delete_old_backups.return_value = 2

        response = client.post(
            '/api/v1/gcp/backups/cleanup?device_id=test-device'
        )

        assert response.status_code == 200
        mock_gcp_service.delete_old_backups.assert_called_once_with(
            'test-device', 5  # Default value
        )

    def test_cleanup_gcp_unavailable(self, client, mock_gcp_service):
        """Test cleanup when GCP unavailable."""
        mock_gcp_service.is_available.return_value = False

        response = client.post(
            '/api/v1/gcp/backups/cleanup?device_id=test-device'
        )

        assert response.status_code == 503


class TestGCPSyncMetadata:
    """Tests for sync metadata operations."""

    def test_create_sync_metadata_success(self, client, mock_gcp_service):
        """Test creating sync metadata."""
        metadata = {
            'device_id': 'test-device',
            'device_name': 'My Device',
            'drive_file_id': 'drive-file-123',
            'last_synced_drive_timestamp': '2024-01-15T10:00:00Z',
            'last_synced_local_timestamp': '2024-01-15T10:00:00Z',
            'sync_status': 'IDLE',
            'conflict_files': []
        }
        mock_gcp_service.create_sync_metadata.return_value = metadata

        response = client.post(
            '/api/v1/gcp/sync-metadata',
            json={
                'device_id': 'test-device',
                'device_name': 'My Device',
                'drive_file_id': 'drive-file-123',
                'last_synced_timestamp': '2024-01-15T10:00:00Z'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['metadata']['device_id'] == 'test-device'

    def test_get_restoration_options_success(self, client, mock_gcp_service):
        """Test getting restoration options."""
        options = {
            'available_backups': 3,
            'backups': [],
            'device_id': 'test-device',
            'latest_backup': {
                'name': 'backup1.db',
                'size_bytes': 1024,
                'created_at': '2024-01-15T10:00:00Z'
            }
        }
        mock_gcp_service.get_backup_restoration_options.return_value = options

        response = client.get('/api/v1/gcp/restoration-options/test-device')

        assert response.status_code == 200
        data = response.json()
        assert data['available_backups'] == 3
        assert data['device_id'] == 'test-device'

    def test_get_restoration_options_gcp_unavailable(self, client, mock_gcp_service):
        """Test getting restoration options when GCP unavailable."""
        mock_gcp_service.is_available.return_value = False

        response = client.get('/api/v1/gcp/restoration-options/test-device')

        assert response.status_code == 503


class TestGCPStatus:
    """Tests for status and health check endpoints."""

    def test_get_gcp_status_success(self, client, mock_gcp_service):
        """Test getting GCP status."""
        status_info = {
            'enabled': True,
            'project_id': 'test-project',
            'location': 'us-central1',
            'gcp_available': True,
            'features': {
                'cloud_storage': True,
                'vertex_ai': True,
                'gemini': False
            }
        }
        mock_gcp_service.get_vertex_ai_info.return_value = status_info

        response = client.get('/api/v1/gcp/status')

        assert response.status_code == 200
        data = response.json()
        assert data['enabled'] is True
        assert data['features']['gemini'] is False

    def test_health_check_healthy(self, client, mock_gcp_service):
        """Test health check when GCP is healthy."""
        mock_gcp_service.is_available.return_value = True
        mock_gcp_service.project_id = 'test-project'

        response = client.get('/api/v1/gcp/health')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        assert data['gcp_available'] is True

    def test_health_check_degraded(self, client, mock_gcp_service):
        """Test health check when GCP is unavailable."""
        mock_gcp_service.is_available.return_value = False

        response = client.get('/api/v1/gcp/health')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'degraded'
        assert data['gcp_available'] is False


class TestGCPErrorHandling:
    """Tests for error handling in GCP endpoints."""

    def test_backup_with_missing_device_id(self, client, mock_gcp_service):
        """Test backup endpoint with missing device_id parameter."""
        response = client.post('/api/v1/gcp/backup')

        # Should handle missing parameter gracefully
        # FastAPI will return 422 for missing required parameters
        assert response.status_code in [422, 400]

    def test_restore_with_invalid_json(self, client, mock_gcp_service):
        """Test restore endpoint with invalid JSON."""
        response = client.post(
            '/api/v1/gcp/restore',
            json={'invalid_field': 'value'}
        )

        # FastAPI validation error
        assert response.status_code == 422

    def test_endpoint_with_gcp_unavailable(self, client, mock_gcp_service):
        """Test all endpoints when GCP service not available."""
        mock_gcp_service.is_available.return_value = False

        endpoints = [
            ('POST', '/api/v1/gcp/backup?device_id=test'),
            ('POST', '/api/v1/gcp/restore?device_id=test&output_path=test.db'),
            ('GET', '/api/v1/gcp/backups'),
        ]

        for method, endpoint in endpoints:
            if method == 'POST':
                response = client.post(endpoint)
            else:
                response = client.get(endpoint)

            assert response.status_code == 503


class TestGCPIntegrationFlow:
    """Tests for complete sync workflows."""

    def test_backup_then_restore_flow(self, client, mock_gcp_service):
        """Test complete backup and restore workflow."""
        # First backup
        mock_gcp_service.upload_db_to_cloud.return_value = 'gs://bucket/backup.db'

        backup_response = client.post('/api/v1/gcp/backup?device_id=test-device')
        assert backup_response.status_code == 200

        # List backups
        mock_gcp_service.list_backups.return_value = [
            {
                'name': 'backup.db',
                'size_bytes': 1024,
                'created_at': '2024-01-15T10:00:00Z',
                'device_id': 'test-device',
                'gcs_uri': 'gs://bucket/backup.db'
            }
        ]

        list_response = client.get('/api/v1/gcp/backups?device_id=test-device')
        assert list_response.status_code == 200
        assert len(list_response.json()) == 1

        # Restore
        mock_gcp_service.download_db_from_cloud.return_value = True

        restore_response = client.post(
            '/api/v1/gcp/restore?device_id=test-device&output_path=mathesis_lab.db'
        )
        assert restore_response.status_code == 200

    def test_sync_metadata_initialization_flow(self, client, mock_gcp_service):
        """Test sync metadata initialization workflow."""
        metadata = {
            'device_id': 'test-device-id',
            'device_name': 'Test Device',
            'drive_file_id': 'drive-123',
            'last_synced_drive_timestamp': '2024-01-15T10:00:00Z',
            'last_synced_local_timestamp': '2024-01-15T10:00:00Z',
            'sync_status': 'IDLE',
            'conflict_files': []
        }
        mock_gcp_service.create_sync_metadata.return_value = metadata

        response = client.post(
            '/api/v1/gcp/sync-metadata',
            json={
                'device_id': 'test-device-id',
                'device_name': 'Test Device',
                'drive_file_id': 'drive-123',
                'last_synced_timestamp': '2024-01-15T10:00:00Z'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data['metadata']['sync_status'] == 'IDLE'

        # Verify sync status
        mock_gcp_service.get_vertex_ai_info.return_value = {
            'enabled': True,
            'project_id': 'test-project',
            'location': 'us-central1',
            'gcp_available': True,
            'features': {'cloud_storage': True, 'vertex_ai': True, 'gemini': False}
        }

        status_response = client.get('/api/v1/gcp/status')
        assert status_response.status_code == 200
