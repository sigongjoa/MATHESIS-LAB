"""
Google Drive Service for MATHESIS LAB - Structure Sync

Provides Mock and Real implementations for Google Drive folder/file management.
"""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
import uuid
from pathlib import Path

# Try to import Google API libraries
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseUpload
    from google.oauth2.credentials import Credentials
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False


class GDriveService(ABC):
    """Abstract base class for Google Drive operations"""
    
    @abstractmethod
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """Create a folder and return its ID"""
        pass
    
    @abstractmethod
    def upload_file(self, file_obj: BinaryIO, filename: str, parent_id: Optional[str] = None) -> str:
        """Upload a file and return its ID"""
        pass
    
    @abstractmethod
    def delete_file(self, file_id: str) -> bool:
        """Delete a file by ID"""
        pass
    
    @abstractmethod
    def get_webview_link(self, file_id: str) -> str:
        """Get the webview link for a file"""
        pass


class MockGDriveService(GDriveService):
    """Mock implementation for development/testing"""
    
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        folder_id = f"mock_folder_{uuid.uuid4().hex[:8]}"
        parent_info = f" (parent: {parent_id})" if parent_id else ""
        print(f"[MockGDrive] Creating folder '{name}'{parent_info} -> ID: {folder_id}")
        return folder_id
    
    def upload_file(self, file_obj: BinaryIO, filename: str, parent_id: Optional[str] = None) -> str:
        file_id = f"mock_file_{uuid.uuid4().hex[:8]}"
        parent_info = f" (parent: {parent_id})" if parent_id else ""
        print(f"[MockGDrive] Uploading file '{filename}'{parent_info} -> ID: {file_id}")
        return file_id
    
    def delete_file(self, file_id: str) -> bool:
        print(f"[MockGDrive] Deleting file: {file_id}")
        return True
    
    def get_webview_link(self, file_id: str) -> str:
        return f"https://drive.google.com/file/d/{file_id}/view"


class RealGDriveService(GDriveService):
    """Real implementation using Google Drive API"""
    
    FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
    
    def __init__(self, credentials: Optional[Credentials] = None, use_service_account: bool = True):
        """
        Initialize Real GDrive Service
        
        Args:
            credentials: OAuth2 credentials (if None, will use service account)
            use_service_account: Whether to use service account credentials
        """
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API libraries not available. Install with: pip install google-api-python-client google-auth")
        
        if credentials:
            self.credentials = credentials
        elif use_service_account:
            self.credentials = self._load_service_account_credentials()
        else:
            raise ValueError("Either credentials or use_service_account=True must be provided")
        
        self.service = build('drive', 'v3', credentials=self.credentials)
    
    def _load_service_account_credentials(self) -> ServiceAccountCredentials:
        """Load service account credentials from config/credentials.json"""
        creds_path = Path(__file__).parent.parent.parent / "config" / "credentials.json"
        
        if not creds_path.exists():
            raise FileNotFoundError(
                f"Service account credentials not found at {creds_path}. "
                "Please download credentials.json from GCP Console."
            )
        
        scopes = ['https://www.googleapis.com/auth/drive.file']
        return ServiceAccountCredentials.from_service_account_file(
            str(creds_path),
            scopes=scopes
        )
    
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        """
        Create a folder in Google Drive
        
        Args:
            name: Folder name
            parent_id: Parent folder ID (None for root)
            
        Returns:
            Created folder ID
        """
        try:
            file_metadata = {
                'name': name,
                'mimeType': self.FOLDER_MIME_TYPE
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name, webViewLink'
            ).execute()
            
            print(f"[RealGDrive] Created folder '{name}' -> ID: {folder['id']}")
            return folder['id']
            
        except HttpError as error:
            print(f"[RealGDrive] Error creating folder: {error}")
            raise
    
    def upload_file(self, file_obj: BinaryIO, filename: str, parent_id: Optional[str] = None) -> str:
        """
        Upload a file to Google Drive
        
        Args:
            file_obj: File-like object to upload
            filename: Name for the file
            parent_id: Parent folder ID (None for root)
            
        Returns:
            Uploaded file ID
        """
        try:
            file_metadata = {'name': filename}
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            # Determine MIME type
            mime_type = 'application/pdf' if filename.endswith('.pdf') else 'application/octet-stream'
            
            media = MediaIoBaseUpload(
                file_obj,
                mimetype=mime_type,
                resumable=True
            )
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            print(f"[RealGDrive] Uploaded file '{filename}' -> ID: {file['id']}")
            return file['id']
            
        except HttpError as error:
            print(f"[RealGDrive] Error uploading file: {error}")
            raise
    
    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from Google Drive
        
        Args:
            file_id: ID of file to delete
            
        Returns:
            True if successful
        """
        try:
            self.service.files().delete(fileId=file_id).execute()
            print(f"[RealGDrive] Deleted file: {file_id}")
            return True
            
        except HttpError as error:
            print(f"[RealGDrive] Error deleting file: {error}")
            return False
    
    def get_webview_link(self, file_id: str) -> str:
        """
        Get the webview link for a file
        
        Args:
            file_id: ID of the file
            
        Returns:
            Webview URL
        """
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()
            
            return file.get('webViewLink', f"https://drive.google.com/file/d/{file_id}/view")
            
        except HttpError as error:
            print(f"[RealGDrive] Error getting webview link: {error}")
            return f"https://drive.google.com/file/d/{file_id}/view"


# Service factory
def get_gdrive_service(use_real: bool = False) -> GDriveService:
    """
    Get GDrive service instance
    
    Args:
        use_real: If True, use real Google Drive API. If False, use mock.
        
    Returns:
        GDriveService instance
    """
    if use_real and GOOGLE_API_AVAILABLE:
        try:
            return RealGDriveService(use_service_account=True)
        except Exception as e:
            print(f"[GDrive] Failed to initialize real service: {e}")
            print("[GDrive] Falling back to mock service")
            return MockGDriveService()
    else:
        return MockGDriveService()


# Global instance - defaults to Mock for safety
# To use real GDrive, set environment variable: GOOGLE_DRIVE_ENABLED=true
import os
USE_REAL_GDRIVE = os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true"
gdrive_service = get_gdrive_service(use_real=USE_REAL_GDRIVE)
