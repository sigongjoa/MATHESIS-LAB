"""
Integration tests for real Google Drive synchronization.

Tests actual Google Drive API interactions with Service Account credentials.
"""

import pytest
from datetime import datetime, UTC
from uuid import uuid4

from backend.app.services.google_drive_service import GoogleDriveService
from backend.app.models.curriculum import Curriculum, Node


class TestGoogleDriveServiceReal:
    """Test actual Google Drive API operations."""

    @pytest.fixture
    def drive_service(self):
        """Create a real Google Drive service instance."""
        return GoogleDriveService(use_service_account=True)

    def test_service_account_initialization(self, drive_service):
        """Test that Service Account credentials are loaded correctly."""
        assert drive_service.service is not None
        assert drive_service.credentials is not None
        assert drive_service.use_service_account is True

    def test_list_files_in_root(self, drive_service):
        """Test listing files in Google Drive root folder."""
        # Query Drive for files in root
        results = drive_service.service.files().list(
            spaces='drive',
            pageSize=10,
            q="trashed=false",
            fields='files(id, name, mimeType, modifiedTime)',
            pageToken=None
        ).execute()

        files = results.get('files', [])
        assert isinstance(files, list)
        print(f"✅ Found {len(files)} files in Google Drive")
        for file in files[:3]:
            print(f"  - {file['name']} ({file['mimeType']})")

    def test_create_curriculum_folder(self, drive_service):
        """Test creating a folder for a curriculum."""
        folder_name = f"test-mathesis-{uuid4().hex[:8]}"

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        folder = drive_service.service.files().create(
            body=file_metadata,
            fields='id, name'
        ).execute()

        assert folder is not None
        assert 'id' in folder
        print(f"✅ Created folder: {folder['name']} (ID: {folder['id']})")

        # Cleanup: delete the folder
        drive_service.service.files().delete(fileId=folder['id']).execute()
        print(f"✅ Deleted test folder")

    def test_upload_file(self, drive_service):
        """Test uploading a JSON file to Drive."""
        import io

        file_name = f"test-node-{uuid4().hex[:8]}.json"
        file_content = b'{"test": "data"}'

        file_metadata = {
            'name': file_name,
            'mimeType': 'application/json'
        }

        media = drive_service.service.files().create(
            body=file_metadata,
            media_body=io.BytesIO(file_content),
            fields='id, name, webViewLink'
        ).execute()

        assert media is not None
        assert 'id' in media
        print(f"✅ Uploaded file: {media['name']} (ID: {media['id']})")
        print(f"   View: {media.get('webViewLink', 'N/A')}")

        # Cleanup: delete the file
        drive_service.service.files().delete(fileId=media['id']).execute()
        print(f"✅ Deleted test file")
