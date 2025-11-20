import uuid
import logging
from typing import Optional, BinaryIO

logger = logging.getLogger(__name__)

class GDriveService:
    """
    Abstract base class / Interface for Google Drive Service.
    """
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        raise NotImplementedError

    def upload_file(self, file_obj: BinaryIO, filename: str, parent_id: Optional[str] = None) -> str:
        raise NotImplementedError

    def delete_file(self, file_id: str) -> None:
        raise NotImplementedError

    def get_webview_link(self, file_id: str) -> str:
        raise NotImplementedError

class MockGDriveService(GDriveService):
    """
    Mock implementation of Google Drive Service for development and testing.
    Returns fake IDs and logs actions.
    """
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        fake_id = f"mock_folder_{uuid.uuid4().hex[:8]}"
        logger.info(f"[MockGDrive] Creating folder '{name}' (parent: {parent_id}) -> ID: {fake_id}")
        return fake_id

    def upload_file(self, file_obj: BinaryIO, filename: str, parent_id: Optional[str] = None) -> str:
        fake_id = f"mock_file_{uuid.uuid4().hex[:8]}"
        logger.info(f"[MockGDrive] Uploading file '{filename}' (parent: {parent_id}) -> ID: {fake_id}")
        return fake_id

    def delete_file(self, file_id: str) -> None:
        logger.info(f"[MockGDrive] Deleting file ID: {file_id}")

    def get_webview_link(self, file_id: str) -> str:
        return f"https://mock.drive.google.com/file/d/{file_id}/view"

# Singleton instance for easy import
# In a real app, use dependency injection
gdrive_service = MockGDriveService()
