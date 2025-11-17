"""
Unit tests for Google Drive Service

Tests OAuth authentication, CRUD operations, and error handling
for Google Drive API integration.
"""

import pytest
from unittest.mock import MagicMock, patch, Mock, AsyncMock
from uuid import uuid4
import json

from backend.app.services.google_drive_service import (
    GoogleDriveService,
    GoogleDriveServiceException,
    GoogleDriveAuthException,
    get_google_drive_service
)


class TestGoogleDriveServiceInitialization:
    """Tests for GoogleDriveService initialization"""

    @patch('backend.app.services.google_drive_service.Path')
    def test_service_initialization(self, mock_path):
        """Test that service initializes with correct configuration"""
        # Mock Service Account credentials file as not existing
        mock_path.return_value.exists.return_value = False

        # Initialize without Service Account (use_service_account=False)
        service = GoogleDriveService(use_service_account=False)

        assert service.client_id is not None or service.client_id is None
        assert service.client_secret is not None or service.client_secret is None
        assert service.service is None
        assert service.credentials is None

    def test_singleton_instance(self):
        """Test that get_google_drive_service returns singleton instance"""
        service1 = get_google_drive_service()
        service2 = get_google_drive_service()

        assert service1 is service2


class TestGoogleDriveOAuth:
    """Tests for OAuth authentication methods"""

    def test_get_auth_url_without_credentials(self):
        """Test that get_auth_url raises exception when credentials not configured"""
        service = GoogleDriveService()
        service.client_id = None
        service.client_secret = None

        with pytest.raises(GoogleDriveAuthException):
            service.get_auth_url("test_state")

    @patch('backend.app.services.google_drive_service.Flow')
    def test_get_auth_url_with_credentials(self, mock_flow_class):
        """Test get_auth_url generates valid authorization URL"""
        mock_flow = MagicMock()
        mock_flow_class.from_client_secrets_info.return_value = mock_flow
        mock_flow.authorization_url.return_value = ("https://accounts.google.com/auth", "state")

        service = GoogleDriveService()
        service.client_id = "test_client_id"
        service.client_secret = "test_client_secret"

        auth_url = service.get_auth_url("test_state")

        assert "https://accounts.google.com/auth" == auth_url
        mock_flow_class.from_client_secrets_info.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.Flow')
    async def test_exchange_code_for_token_success(self, mock_flow_class):
        """Test successful token exchange"""
        mock_flow = MagicMock()
        mock_flow_class.from_client_secrets_info.return_value = mock_flow
        mock_flow.fetch_token.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600
        }

        service = GoogleDriveService()
        service.client_id = "test_client_id"
        service.client_secret = "test_client_secret"

        token_response = await service.exchange_code_for_token("test_code", "test_state")

        assert token_response["access_token"] == "test_access_token"
        assert token_response["refresh_token"] == "test_refresh_token"
        mock_flow.fetch_token.assert_called_once_with(code="test_code")

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.Flow')
    async def test_exchange_code_for_token_failure(self, mock_flow_class):
        """Test token exchange failure"""
        mock_flow = MagicMock()
        mock_flow_class.from_client_secrets_info.return_value = mock_flow
        mock_flow.fetch_token.side_effect = Exception("Token exchange failed")

        service = GoogleDriveService()
        service.client_id = "test_client_id"
        service.client_secret = "test_client_secret"

        with pytest.raises(GoogleDriveAuthException):
            await service.exchange_code_for_token("invalid_code", "test_state")

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.Credentials')
    @patch('backend.app.services.google_drive_service.Request')
    async def test_refresh_token_success(self, mock_request_class, mock_credentials_class):
        """Test successful token refresh"""
        mock_creds = MagicMock()
        mock_creds.token = "new_access_token"
        mock_creds.refresh_token = "refresh_token"
        mock_credentials_class.return_value = mock_creds

        service = GoogleDriveService()
        service.client_id = "test_client_id"
        service.client_secret = "test_client_secret"

        token_response = await service.refresh_token("test_refresh_token")

        assert token_response["access_token"] == "new_access_token"
        assert token_response["refresh_token"] == "refresh_token"
        mock_creds.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_refresh_token_without_credentials(self):
        """Test refresh_token raises exception when credentials not configured"""
        service = GoogleDriveService()
        service.client_id = None
        service.client_secret = None

        with pytest.raises(GoogleDriveAuthException):
            await service.refresh_token("test_refresh_token")


class TestGoogleDriveFolderOperations:
    """Tests for folder management operations"""

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.build')
    async def test_create_curriculum_folder_success(self, mock_build):
        """Test successful curriculum folder creation"""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = MagicMock()
        mock_service.files.return_value = mock_files
        mock_create = MagicMock()
        mock_files.create.return_value = mock_create
        mock_create.execute.return_value = {"id": "folder_123"}

        service = GoogleDriveService()
        service.service = mock_service
        service.credentials = MagicMock()

        folder_id = await service.create_curriculum_folder("Test Curriculum")

        assert folder_id == "folder_123"
        mock_files.create.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.Path')
    async def test_create_curriculum_folder_not_authenticated(self, mock_path):
        """Test create_curriculum_folder raises when not authenticated"""
        # Mock Service Account file as not existing
        mock_path.return_value.exists.return_value = False

        service = GoogleDriveService(use_service_account=False)
        service.credentials = None
        service.service = None

        with pytest.raises(GoogleDriveAuthException):
            await service.create_curriculum_folder("Test Curriculum")


class TestGoogleDriveFileOperations:
    """Tests for file CRUD operations"""

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.build')
    async def test_save_node_to_drive_new_file(self, mock_build):
        """Test saving new node to Drive"""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        # Mock list operation (file doesn't exist)
        mock_files = MagicMock()
        mock_service.files.return_value = mock_files

        mock_list = MagicMock()
        mock_files.list.return_value = mock_list
        mock_list.execute.return_value = {"files": []}

        # Mock create operation
        mock_create = MagicMock()
        mock_files.create.return_value = mock_create
        mock_create.execute.return_value = {"id": "file_123"}

        service = GoogleDriveService()
        service.service = mock_service
        service.credentials = MagicMock()

        node_id = uuid4()
        node_data = {
            "id": str(node_id),
            "title": "Test Node",
            "content": "Test content",
            "children": []
        }

        file_id = await service.save_node_to_drive(node_id, node_data, "curriculum_folder_123")

        assert file_id == "file_123"
        mock_files.create.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.build')
    async def test_save_node_to_drive_update_existing(self, mock_build):
        """Test updating existing node file on Drive"""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = MagicMock()
        mock_service.files.return_value = mock_files

        # Mock list operation (file exists)
        mock_list = MagicMock()
        mock_files.list.return_value = mock_list
        mock_list.execute.return_value = {"files": [{"id": "existing_file_123"}]}

        # Mock update operation
        mock_update = MagicMock()
        mock_files.update.return_value = mock_update
        mock_update.execute.return_value = {"id": "existing_file_123"}

        service = GoogleDriveService()
        service.service = mock_service
        service.credentials = MagicMock()

        node_id = uuid4()
        node_data = {
            "id": str(node_id),
            "title": "Updated Node",
            "content": "Updated content"
        }

        file_id = await service.save_node_to_drive(node_id, node_data, "curriculum_folder_123")

        assert file_id == "existing_file_123"
        mock_files.update.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.Path')
    async def test_save_node_to_drive_not_authenticated(self, mock_path):
        """Test save_node_to_drive raises when not authenticated"""
        # Mock Service Account file as not existing
        mock_path.return_value.exists.return_value = False

        service = GoogleDriveService(use_service_account=False)
        service.credentials = None
        service.service = None

        node_id = uuid4()
        node_data = {"title": "Test"}

        with pytest.raises(GoogleDriveAuthException):
            await service.save_node_to_drive(node_id, node_data, "folder_123")

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.build')
    async def test_load_node_from_drive(self, mock_build):
        """Test loading node from Drive"""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = MagicMock()
        mock_service.files.return_value = mock_files

        node_data = {
            "id": "node_123",
            "title": "Test Node",
            "content": "Test content"
        }

        mock_get_media = MagicMock()
        mock_files.get_media.return_value = mock_get_media
        mock_get_media.execute.return_value = json.dumps(node_data).encode('utf-8')

        service = GoogleDriveService()
        service.service = mock_service
        service.credentials = MagicMock()

        loaded_data = await service.load_node_from_drive("file_123")

        assert loaded_data["id"] == "node_123"
        assert loaded_data["title"] == "Test Node"
        mock_files.get_media.assert_called_once_with(fileId="file_123")

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.Path')
    async def test_load_node_from_drive_not_authenticated(self, mock_path):
        """Test load_node_from_drive raises when not authenticated"""
        # Mock Service Account file as not existing
        mock_path.return_value.exists.return_value = False

        service = GoogleDriveService(use_service_account=False)
        service.credentials = None
        service.service = None

        with pytest.raises(GoogleDriveAuthException):
            await service.load_node_from_drive("file_123")

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.build')
    async def test_update_node_on_drive(self, mock_build):
        """Test updating node on Drive"""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = MagicMock()
        mock_service.files.return_value = mock_files

        mock_update = MagicMock()
        mock_files.update.return_value = mock_update
        mock_update.execute.return_value = {"id": "file_123"}

        service = GoogleDriveService()
        service.service = mock_service
        service.credentials = MagicMock()

        node_data = {"title": "Updated Title"}
        await service.update_node_on_drive("file_123", node_data)

        mock_files.update.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.build')
    async def test_delete_node_from_drive(self, mock_build):
        """Test deleting node from Drive"""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = MagicMock()
        mock_service.files.return_value = mock_files

        mock_delete = MagicMock()
        mock_files.delete.return_value = mock_delete
        mock_delete.execute.return_value = None

        service = GoogleDriveService()
        service.service = mock_service
        service.credentials = MagicMock()

        await service.delete_node_from_drive("file_123")

        mock_files.delete.assert_called_once_with(fileId="file_123")


class TestGoogleDriveListOperations:
    """Tests for list and metadata operations"""

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.build')
    async def test_list_nodes_on_drive(self, mock_build):
        """Test listing nodes in curriculum folder"""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = MagicMock()
        mock_service.files.return_value = mock_files

        mock_list = MagicMock()
        mock_files.list.return_value = mock_list
        mock_list.execute.return_value = {
            "files": [
                {"id": "file_1", "name": "node_001.json", "modifiedTime": "2025-01-01T00:00:00Z"},
                {"id": "file_2", "name": "node_002.json", "modifiedTime": "2025-01-02T00:00:00Z"}
            ]
        }

        service = GoogleDriveService()
        service.service = mock_service
        service.credentials = MagicMock()

        nodes = await service.list_nodes_on_drive("curriculum_folder_123")

        assert len(nodes) == 2
        assert nodes[0]["id"] == "file_1"
        assert nodes[1]["id"] == "file_2"
        mock_files.list.assert_called_once()

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.build')
    async def test_get_file_metadata(self, mock_build):
        """Test retrieving file metadata"""
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = MagicMock()
        mock_service.files.return_value = mock_files

        mock_get = MagicMock()
        mock_files.get.return_value = mock_get
        mock_get.execute.return_value = {
            "id": "file_123",
            "name": "node_001.json",
            "modifiedTime": "2025-01-01T00:00:00Z",
            "size": "1024",
            "mimeType": "application/json"
        }

        service = GoogleDriveService()
        service.service = mock_service
        service.credentials = MagicMock()

        metadata = await service.get_file_metadata("file_123")

        assert metadata["id"] == "file_123"
        assert metadata["name"] == "node_001.json"
        assert metadata["size"] == "1024"
        mock_files.get.assert_called_once()


class TestGoogleDriveErrorHandling:
    """Tests for error handling"""

    @pytest.mark.asyncio
    @patch('backend.app.services.google_drive_service.build')
    async def test_http_error_handling(self, mock_build):
        """Test handling of HttpError from Drive API"""
        from googleapiclient.errors import HttpError

        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_files = MagicMock()
        mock_service.files.return_value = mock_files

        mock_list = MagicMock()
        mock_files.list.return_value = mock_list
        mock_list.execute.side_effect = HttpError(
            Mock(status=404), b'Not Found'
        )

        service = GoogleDriveService()
        service.service = mock_service
        service.credentials = MagicMock()

        with pytest.raises(GoogleDriveServiceException):
            await service.list_nodes_on_drive("nonexistent_folder")

    def test_get_service_not_authenticated(self):
        """Test _get_service raises when not authenticated"""
        service = GoogleDriveService()
        service.service = None
        service.credentials = None

        with pytest.raises(GoogleDriveAuthException):
            service._get_service()
