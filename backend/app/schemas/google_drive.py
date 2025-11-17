"""
Schemas for Google Drive API Integration

Defines request/response models for Google Drive OAuth and file operations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GoogleDriveAuthUrlRequest(BaseModel):
    """Request to generate Google Drive OAuth authorization URL"""
    state: str = Field(..., description="CSRF token for security")


class GoogleDriveAuthUrlResponse(BaseModel):
    """Response containing OAuth authorization URL"""
    auth_url: str = Field(..., description="Google Drive OAuth authorization URL")
    state: str = Field(..., description="CSRF token (for verification)")


class GoogleDriveTokenRequest(BaseModel):
    """Request for token exchange"""
    code: str = Field(..., description="Authorization code from Google")
    state: str = Field(..., description="CSRF token (must match)")


class GoogleDriveTokenResponse(BaseModel):
    """Response containing OAuth tokens"""
    access_token: str = Field(..., description="Access token for Drive API")
    refresh_token: Optional[str] = Field(None, description="Refresh token for offline access")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    token_type: str = Field(default="Bearer", description="Token type")


class GoogleDriveRefreshTokenRequest(BaseModel):
    """Request to refresh an expired access token"""
    refresh_token: str = Field(..., description="Refresh token")


class CreateCurriculumFolderRequest(BaseModel):
    """Request to create a curriculum folder on Drive"""
    curriculum_name: str = Field(..., description="Name of the curriculum")
    parent_folder_id: Optional[str] = Field(None, description="Parent folder ID (optional)")


class CreateCurriculumFolderResponse(BaseModel):
    """Response from curriculum folder creation"""
    folder_id: str = Field(..., description="Google Drive folder ID")
    curriculum_name: str = Field(..., description="Curriculum name")


class SaveNodeRequest(BaseModel):
    """Request to save a node to Google Drive"""
    node_id: str = Field(..., description="Node UUID")
    node_data: dict = Field(..., description="Node data (title, content, children, etc.)")
    curriculum_folder_id: str = Field(..., description="Curriculum folder ID on Drive")


class SaveNodeResponse(BaseModel):
    """Response from node save operation"""
    file_id: str = Field(..., description="Google Drive file ID")
    node_id: str = Field(..., description="Node UUID")


class UpdateNodeRequest(BaseModel):
    """Request to update an existing node on Drive"""
    file_id: str = Field(..., description="Google Drive file ID")
    node_data: dict = Field(..., description="Updated node data")


class LoadNodeResponse(BaseModel):
    """Response from loading a node from Drive"""
    node_id: str = Field(..., description="Node UUID")
    node_data: dict = Field(..., description="Complete node data")


class FileMetadata(BaseModel):
    """File metadata from Google Drive"""
    file_id: str = Field(..., description="Google Drive file ID")
    name: str = Field(..., description="File name")
    modified_time: Optional[str] = Field(None, description="Last modification time")
    size: Optional[str] = Field(None, description="File size in bytes")
    mime_type: Optional[str] = Field(None, description="MIME type")


class ListNodesResponse(BaseModel):
    """Response from listing nodes in a curriculum"""
    nodes: List[FileMetadata] = Field(..., description="List of node files")
    count: int = Field(..., description="Total number of nodes")


class SyncStatusResponse(BaseModel):
    """Response showing current sync status"""
    is_authenticated: bool = Field(..., description="Whether user is authenticated with Drive")
    last_sync_time: Optional[datetime] = Field(None, description="Last sync timestamp")
    curriculum_folders: int = Field(0, description="Number of synced curriculum folders")
    pending_changes: int = Field(0, description="Number of pending changes to sync")


class GoogleDriveErrorResponse(BaseModel):
    """Error response from Google Drive API"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
