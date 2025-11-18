"""
Google Drive Service for MATHESIS LAB

Manages interaction with Google Drive API for node storage and synchronization.
Provides methods for:
- Authentication via OAuth 2.0
- CRUD operations on nodes (stored as JSON files)
- Folder management for curriculums
- File metadata tracking
"""

import json
import os
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, UTC
from io import BytesIO
from pathlib import Path
import pickle

from backend.app.core.config import settings

# Optional Google API imports for CI/CD compatibility
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google.oauth2.service_account import Credentials as ServiceAccountCredentials
    from google_auth_oauthlib.flow import Flow
    GOOGLE_API_AVAILABLE = True
except ImportError:
    # For CI/CD environments without Google API libraries
    GOOGLE_API_AVAILABLE = False
    build = None
    HttpError = Exception
    Request = None
    Credentials = None
    ServiceAccountCredentials = None
    Flow = None


class GoogleDriveServiceException(Exception):
    """Base exception for Google Drive service errors"""
    pass


class GoogleDriveAuthException(GoogleDriveServiceException):
    """Exception for authentication-related errors"""
    pass


class GoogleDriveService:
    """
    Service for managing Google Drive integration.

    Handles OAuth authentication, file operations, and folder management
    for storing curriculum nodes as JSON files on Google Drive.
    """

    # MIME types for Drive operations
    FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
    JSON_MIME_TYPE = "application/json"

    # Scopes needed for Drive API
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.readonly'
    ]

    def __init__(self, use_service_account: bool = True):
        """
        Initialize Google Drive Service.

        Args:
            use_service_account: If True, use Service Account credentials for server-to-server auth.
                                If False, use OAuth 2.0 for user authentication.
        """
        self.client_id = settings.GOOGLE_OAUTH_CLIENT_ID
        self.client_secret = settings.GOOGLE_OAUTH_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_DRIVE_REDIRECT_URI
        self.root_folder_id = settings.GOOGLE_DRIVE_CURRICULUM_FOLDER_ID

        self.service = None
        self.credentials = None
        self.use_service_account = use_service_account

        # Initialize with Service Account if available
        if use_service_account:
            self._initialize_service_account()

    def _initialize_service_account(self):
        """Initialize Google Drive service with Service Account credentials."""
        creds_path = Path(__file__).parent.parent.parent / "config" / "credentials.json"

        if not creds_path.exists():
            raise GoogleDriveAuthException(
                f"Service Account credentials not found at {creds_path}. "
                "Please download credentials.json from GCP console and place it in backend/config/"
            )

        try:
            self.credentials = ServiceAccountCredentials.from_service_account_file(
                str(creds_path),
                scopes=self.SCOPES
            )
            self.service = build('drive', 'v3', credentials=self.credentials)
        except Exception as e:
            raise GoogleDriveAuthException(f"Failed to initialize Service Account: {str(e)}")

    def get_auth_url(self, state: str) -> str:
        """
        Generate Google OAuth authorization URL.

        Args:
            state: CSRF token for security

        Returns:
            Authorization URL for redirecting user to Google OAuth consent screen

        Raises:
            GoogleDriveAuthException: If credentials are not configured
        """
        if not self.client_id or not self.client_secret:
            raise GoogleDriveAuthException(
                "Google Drive credentials not configured. "
                "Set GOOGLE_DRIVE_CLIENT_ID and GOOGLE_DRIVE_CLIENT_SECRET in .env"
            )

        flow = Flow.from_client_secrets_info(
            {
                "installed": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.SCOPES,
            state=state
        )

        flow.redirect_uri = self.redirect_uri
        auth_url, state = flow.authorization_url(access_type='offline', prompt='consent')
        return auth_url

    async def exchange_code_for_token(self, code: str, state: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from Google OAuth flow
            state: CSRF token for validation

        Returns:
            Token response with access_token, refresh_token, etc.

        Raises:
            GoogleDriveAuthException: If token exchange fails
        """
        if not self.client_id or not self.client_secret:
            raise GoogleDriveAuthException("Google Drive credentials not configured")

        flow = Flow.from_client_secrets_info(
            {
                "installed": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [self.redirect_uri],
                }
            },
            scopes=self.SCOPES,
            state=state
        )

        flow.redirect_uri = self.redirect_uri

        try:
            token_response = flow.fetch_token(code=code)
            self.credentials = flow.credentials
            return token_response
        except Exception as e:
            raise GoogleDriveAuthException(f"Failed to exchange code for token: {str(e)}")

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh expired access token using refresh token.

        Args:
            refresh_token: Refresh token from previous authentication

        Returns:
            New token response with updated access_token

        Raises:
            GoogleDriveAuthException: If token refresh fails
        """
        try:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                id_token=None,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret
            )

            request = Request()
            credentials.refresh(request)

            self.credentials = credentials

            return {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "expires_in": 3600,
            }
        except Exception as e:
            raise GoogleDriveAuthException(f"Failed to refresh token: {str(e)}")

    def set_credentials(self, credentials: Credentials) -> None:
        """
        Set credentials for Drive API access.

        Args:
            credentials: Google OAuth credentials
        """
        self.credentials = credentials
        self.service = build('drive', 'v3', credentials=credentials)

    def _get_service(self) -> Any:
        """
        Get or create Drive API service.

        Returns:
            Google Drive API service instance

        Raises:
            GoogleDriveAuthException: If service cannot be initialized
        """
        if self.service is None:
            if self.credentials is None:
                raise GoogleDriveAuthException("Not authenticated with Google Drive")
            self.service = build('drive', 'v3', credentials=self.credentials)
        return self.service

    async def create_curriculum_folder(self, curriculum_name: str, parent_folder_id: Optional[str] = None) -> str:
        """
        Create a folder for curriculum on Google Drive.

        Args:
            curriculum_name: Name of the curriculum
            parent_folder_id: Parent folder ID (defaults to root)

        Returns:
            ID of created folder

        Raises:
            GoogleDriveServiceException: If folder creation fails
        """
        if parent_folder_id is None:
            parent_folder_id = self.root_folder_id

        try:
            service = self._get_service()

            file_metadata = {
                'name': curriculum_name,
                'mimeType': self.FOLDER_MIME_TYPE,
                'parents': [parent_folder_id]
            }

            folder = service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            return folder.get('id')
        except HttpError as e:
            raise GoogleDriveServiceException(f"Failed to create curriculum folder: {str(e)}")

    async def save_node_to_drive(
        self,
        node_id: UUID,
        node_data: Dict[str, Any],
        curriculum_folder_id: str
    ) -> str:
        """
        Save node as JSON file to Google Drive.

        Args:
            node_id: UUID of the node
            node_data: Node data as dictionary (includes title, content, children, etc.)
            curriculum_folder_id: Curriculum folder ID on Drive

        Returns:
            Google Drive file ID of created/updated node file

        Raises:
            GoogleDriveServiceException: If file upload fails
        """
        try:
            service = self._get_service()

            # Prepare file metadata
            file_name = f"node_{str(node_id)}.json"

            # Check if file already exists
            existing_files = service.files().list(
                q=f"name='{file_name}' and '{curriculum_folder_id}' in parents and trashed=false",
                spaces='drive',
                fields='files(id)',
                pageSize=1
            ).execute()

            file_id = None
            if existing_files.get('files'):
                file_id = existing_files['files'][0]['id']

            # Prepare JSON content
            json_content = json.dumps(node_data, default=str, indent=2)

            if file_id:
                # Update existing file
                service.files().update(
                    fileId=file_id,
                    body={'mimeType': self.JSON_MIME_TYPE},
                    media_body=BytesIO(json_content.encode('utf-8')),
                    fields='id'
                ).execute()
                return file_id
            else:
                # Create new file
                file_metadata = {
                    'name': file_name,
                    'parents': [curriculum_folder_id],
                    'mimeType': self.JSON_MIME_TYPE
                }

                file_obj = service.files().create(
                    body=file_metadata,
                    media_body=BytesIO(json_content.encode('utf-8')),
                    fields='id'
                ).execute()

                return file_obj.get('id')

        except HttpError as e:
            raise GoogleDriveServiceException(f"Failed to save node to Drive: {str(e)}")

    async def load_node_from_drive(self, file_id: str) -> Dict[str, Any]:
        """
        Load node data from Google Drive JSON file.

        Args:
            file_id: Google Drive file ID

        Returns:
            Node data as dictionary

        Raises:
            GoogleDriveServiceException: If file download fails
        """
        try:
            service = self._get_service()

            content = service.files().get_media(fileId=file_id).execute()
            node_data = json.loads(content.decode('utf-8'))
            return node_data

        except HttpError as e:
            raise GoogleDriveServiceException(f"Failed to load node from Drive: {str(e)}")

    async def update_node_on_drive(self, file_id: str, node_data: Dict[str, Any]) -> None:
        """
        Update existing node file on Google Drive.

        Args:
            file_id: Google Drive file ID
            node_data: Updated node data

        Raises:
            GoogleDriveServiceException: If file update fails
        """
        try:
            service = self._get_service()

            json_content = json.dumps(node_data, default=str, indent=2)

            service.files().update(
                fileId=file_id,
                media_body=BytesIO(json_content.encode('utf-8')),
                fields='id'
            ).execute()

        except HttpError as e:
            raise GoogleDriveServiceException(f"Failed to update node on Drive: {str(e)}")

    async def delete_node_from_drive(self, file_id: str) -> None:
        """
        Delete node file from Google Drive.

        Args:
            file_id: Google Drive file ID

        Raises:
            GoogleDriveServiceException: If file deletion fails
        """
        try:
            service = self._get_service()
            service.files().delete(fileId=file_id).execute()
        except HttpError as e:
            raise GoogleDriveServiceException(f"Failed to delete node from Drive: {str(e)}")

    async def list_nodes_on_drive(self, curriculum_folder_id: str) -> List[Dict[str, Any]]:
        """
        List all node files in a curriculum folder on Drive.

        Args:
            curriculum_folder_id: Curriculum folder ID on Drive

        Returns:
            List of file metadata dictionaries with id, name, modifiedTime

        Raises:
            GoogleDriveServiceException: If listing fails
        """
        try:
            service = self._get_service()

            files = service.files().list(
                q=f"'{curriculum_folder_id}' in parents and mimeType='{self.JSON_MIME_TYPE}' and trashed=false",
                spaces='drive',
                fields='files(id, name, modifiedTime)',
                pageSize=100
            ).execute()

            return files.get('files', [])

        except HttpError as e:
            raise GoogleDriveServiceException(f"Failed to list nodes on Drive: {str(e)}")

    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Get file metadata from Google Drive (modification time, size, etc.).

        Args:
            file_id: Google Drive file ID

        Returns:
            File metadata dictionary

        Raises:
            GoogleDriveServiceException: If metadata retrieval fails
        """
        try:
            service = self._get_service()

            metadata = service.files().get(
                fileId=file_id,
                fields='id, name, modifiedTime, size, mimeType'
            ).execute()

            return metadata

        except HttpError as e:
            raise GoogleDriveServiceException(f"Failed to get file metadata: {str(e)}")

    async def move_file_to_trash(self, file_id: str) -> None:
        """
        Move file to trash instead of permanent deletion.

        Args:
            file_id: Google Drive file ID

        Raises:
            GoogleDriveServiceException: If operation fails
        """
        try:
            service = self._get_service()

            service.files().update(
                fileId=file_id,
                body={'trashed': True}
            ).execute()

        except HttpError as e:
            raise GoogleDriveServiceException(f"Failed to move file to trash: {str(e)}")


# Singleton instance for application-wide use
_google_drive_service_instance: Optional[GoogleDriveService] = None


def get_google_drive_service() -> GoogleDriveService:
    """
    Get or create Google Drive service instance.

    Returns:
        GoogleDriveService instance
    """
    global _google_drive_service_instance
    if _google_drive_service_instance is None:
        _google_drive_service_instance = GoogleDriveService()
    return _google_drive_service_instance
