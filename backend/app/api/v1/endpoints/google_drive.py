"""
Google Drive Integration Endpoints for MATHESIS LAB

Provides REST API endpoints for Google Drive authentication and node synchronization.
Implements OAuth 2.0 flow for user authorization with Google Drive.
"""

from fastapi import APIRouter, HTTPException, status
from uuid import UUID
import secrets

from backend.app.services.google_drive_service import (
    GoogleDriveService,
    get_google_drive_service,
    GoogleDriveAuthException,
    GoogleDriveServiceException
)
from backend.app.schemas.google_drive import (
    GoogleDriveAuthUrlRequest,
    GoogleDriveAuthUrlResponse,
    GoogleDriveTokenRequest,
    GoogleDriveTokenResponse,
    GoogleDriveRefreshTokenRequest,
    CreateCurriculumFolderRequest,
    CreateCurriculumFolderResponse,
    SaveNodeRequest,
    SaveNodeResponse,
    UpdateNodeRequest,
    LoadNodeResponse,
    ListNodesResponse,
    FileMetadata,
    SyncStatusResponse,
    GoogleDriveErrorResponse,
)

router = APIRouter(prefix="/google-drive", tags=["google-drive"])


@router.post(
    "/auth/start",
    response_model=GoogleDriveAuthUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Start Google Drive OAuth flow",
    responses={
        200: {"description": "Authorization URL generated successfully"},
        500: {"description": "Google Drive credentials not configured"},
    }
)
async def start_oauth_flow(
    request: GoogleDriveAuthUrlRequest,
) -> GoogleDriveAuthUrlResponse:
    """
    Generate Google Drive OAuth authorization URL.

    **Request Body:**
    - state: CSRF token for security (should be random string)

    **Returns:**
    - auth_url: URL to redirect user to Google consent screen
    - state: Echo back of CSRF token

    **Usage:**
    1. Client generates random state token
    2. Client calls this endpoint with state
    3. Client redirects user to returned auth_url
    4. User logs in and grants permissions
    5. Google redirects to callback with code
    6. Client exchanges code for tokens at /google-drive/auth/callback
    """
    service = get_google_drive_service()
    auth_url = service.get_auth_url(request.state)

    return GoogleDriveAuthUrlResponse(
        auth_url=auth_url,
        state=request.state
    )


@router.post(
    "/auth/callback",
    response_model=GoogleDriveTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle Google Drive OAuth callback",
    responses={
        200: {"description": "Token exchange successful"},
        400: {"description": "Invalid authorization code or state"},
        500: {"description": "Token exchange failed"},
    }
)
async def handle_oauth_callback(
    request: GoogleDriveTokenRequest,
) -> GoogleDriveTokenResponse:
    """
    Exchange authorization code for access/refresh tokens.

    **Request Body:**
    - code: Authorization code from Google OAuth flow
    - state: CSRF token (must match the one sent to /auth/start)

    **Returns:**
    - access_token: Token for API requests (expires in ~1 hour)
    - refresh_token: Token to get new access token offline
    - expires_in: Seconds until access_token expires
    - token_type: Always "Bearer"

    **Usage:**
    1. Google redirects user to callback with code and state
    2. Client sends code and state to this endpoint
    3. Backend exchanges code for tokens
    4. Client stores refresh_token securely
    5. Client uses access_token for API requests
    6. When access_token expires, refresh using /auth/refresh
    """
    service = get_google_drive_service()
    token_response = await service.exchange_code_for_token(
        request.code,
        request.state
    )

    return GoogleDriveTokenResponse(
        access_token=token_response.get("access_token", ""),
        refresh_token=token_response.get("refresh_token"),
        expires_in=token_response.get("expires_in", 3600),
    )


@router.post(
    "/auth/refresh",
    response_model=GoogleDriveTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh expired access token",
    responses={
        200: {"description": "Token refreshed successfully"},
        400: {"description": "Invalid refresh token"},
        500: {"description": "Token refresh failed"},
    }
)
async def refresh_access_token(
    request: GoogleDriveRefreshTokenRequest,
) -> GoogleDriveTokenResponse:
    """
    Refresh an expired access token using refresh token.

    **Request Body:**
    - refresh_token: Refresh token from previous authentication

    **Returns:**
    - access_token: New access token for API requests
    - refresh_token: Same refresh token (can be reused)
    - expires_in: Seconds until new access_token expires

    **Usage:**
    When access_token expires:
    1. Client sends refresh_token to this endpoint
    2. Backend gets new access_token
    3. Client continues using API with new access_token
    """
    service = get_google_drive_service()
    token_response = await service.refresh_token(request.refresh_token)

    return GoogleDriveTokenResponse(
        access_token=token_response.get("access_token", ""),
        refresh_token=token_response.get("refresh_token", request.refresh_token),
        expires_in=token_response.get("expires_in", 3600),
    )


@router.post(
    "/curriculum/create-folder",
    response_model=CreateCurriculumFolderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create curriculum folder on Google Drive",
    responses={
        201: {"description": "Curriculum folder created successfully"},
        401: {"description": "Not authenticated with Google Drive"},
        500: {"description": "Failed to create folder"},
    }
)
async def create_curriculum_folder(
    request: CreateCurriculumFolderRequest,
) -> CreateCurriculumFolderResponse:
    """
    Create a folder on Google Drive for storing curriculum nodes.

    **Request Body:**
    - curriculum_name: Name of the curriculum
    - parent_folder_id: Parent folder ID (optional, defaults to root)

    **Returns:**
    - folder_id: Google Drive folder ID for this curriculum
    - curriculum_name: Name of created folder

    **Usage:**
    When creating a new curriculum that should sync with Drive:
    1. Get access_token for Drive API
    2. Call this endpoint with curriculum name
    3. Store returned folder_id in curriculum metadata
    4. Use folder_id for storing nodes (node files go in this folder)
    """
    service = get_google_drive_service()
    folder_id = await service.create_curriculum_folder(
        request.curriculum_name,
        request.parent_folder_id
    )

    return CreateCurriculumFolderResponse(
        folder_id=folder_id,
        curriculum_name=request.curriculum_name
    )


@router.post(
    "/nodes/save",
    response_model=SaveNodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save node to Google Drive",
    responses={
        201: {"description": "Node saved successfully"},
        400: {"description": "Invalid node data"},
        401: {"description": "Not authenticated with Google Drive"},
        500: {"description": "Failed to save node"},
    }
)
async def save_node_to_drive(
    request: SaveNodeRequest,
) -> SaveNodeResponse:
    """
    Save or update a node as JSON file on Google Drive.

    **Request Body:**
    - node_id: Node UUID
    - node_data: Complete node data (title, content, children, metadata)
    - curriculum_folder_id: Curriculum folder ID on Drive

    **Returns:**
    - file_id: Google Drive file ID for this node
    - node_id: Node UUID (echoed back)

    **Node Data Format:**
    ```json
    {
      "id": "node_uuid",
      "title": "Node Title",
      "content": "Markdown content",
      "created_at": "ISO datetime",
      "modified_at": "ISO datetime",
      "children": ["child_node_id_1", "child_node_id_2"],
      "metadata": { ... }
    }
    ```

    **Usage:**
    When saving a node (create or update):
    1. Prepare node_data with all required fields
    2. Call this endpoint with node_data
    3. Returns file_id for this node on Drive
    4. Store file_id in SyncMetadata for future updates
    """
    service = get_google_drive_service()
    file_id = await service.save_node_to_drive(
        UUID(request.node_id),
        request.node_data,
        request.curriculum_folder_id
    )

    return SaveNodeResponse(
        file_id=file_id,
        node_id=request.node_id
    )


@router.get(
    "/nodes/{file_id}",
    response_model=LoadNodeResponse,
    status_code=status.HTTP_200_OK,
    summary="Load node from Google Drive",
    responses={
        200: {"description": "Node loaded successfully"},
        401: {"description": "Not authenticated with Google Drive"},
        404: {"description": "Node file not found"},
        500: {"description": "Failed to load node"},
    }
)
async def load_node_from_drive(
    file_id: str,
) -> LoadNodeResponse:
    """
    Load node data from Google Drive JSON file.

    **Path Parameters:**
    - file_id: Google Drive file ID

    **Returns:**
    - node_id: Node UUID
    - node_data: Complete node data

    **Usage:**
    When syncing down changes from Drive:
    1. Get file_id from SyncMetadata for the node
    2. Call this endpoint with file_id
    3. Returns current node_data from Drive
    4. Compare with local version and merge/update as needed
    """
    service = get_google_drive_service()
    node_data = await service.load_node_from_drive(file_id)

    return LoadNodeResponse(
        node_id=node_data.get("id", ""),
        node_data=node_data
    )


@router.put(
    "/nodes/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update node on Google Drive",
    responses={
        204: {"description": "Node updated successfully"},
        401: {"description": "Not authenticated with Google Drive"},
        404: {"description": "Node file not found"},
        500: {"description": "Failed to update node"},
    }
)
async def update_node_on_drive(
    file_id: str,
    request: UpdateNodeRequest,
) -> None:
    """
    Update existing node on Google Drive.

    **Path Parameters:**
    - file_id: Google Drive file ID

    **Request Body:**
    - node_data: Updated node data

    **Usage:**
    When syncing up changes to Drive:
    1. Get file_id from SyncMetadata
    2. Prepare updated node_data
    3. Call this endpoint to update file
    4. Returns 204 No Content on success
    """
    service = get_google_drive_service()
    await service.update_node_on_drive(request.file_id, request.node_data)


@router.delete(
    "/nodes/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete node from Google Drive",
    responses={
        204: {"description": "Node deleted successfully"},
        401: {"description": "Not authenticated with Google Drive"},
        404: {"description": "Node file not found"},
        500: {"description": "Failed to delete node"},
    }
)
async def delete_node_from_drive(
    file_id: str,
) -> None:
    """
    Delete node file from Google Drive.

    **Path Parameters:**
    - file_id: Google Drive file ID

    **Usage:**
    When deleting a node from curriculum:
    1. Get file_id from SyncMetadata
    2. Call this endpoint to delete from Drive
    3. Update local database to mark as deleted
    """
    service = get_google_drive_service()
    await service.delete_node_from_drive(file_id)


@router.get(
    "/curriculum/{curriculum_folder_id}/nodes",
    response_model=ListNodesResponse,
    status_code=status.HTTP_200_OK,
    summary="List nodes in curriculum folder",
    responses={
        200: {"description": "Node list retrieved successfully"},
        401: {"description": "Not authenticated with Google Drive"},
        500: {"description": "Failed to list nodes"},
    }
)
async def list_nodes_on_drive(
    curriculum_folder_id: str,
) -> ListNodesResponse:
    """
    List all node files in a curriculum folder.

    **Path Parameters:**
    - curriculum_folder_id: Google Drive curriculum folder ID

    **Returns:**
    - nodes: List of file metadata (id, name, modified_time)
    - count: Total number of nodes

    **Usage:**
    When syncing curriculum:
    1. Get curriculum_folder_id from curriculum metadata
    2. Call this endpoint to get list of files
    3. Compare with local nodes to detect:
       - New nodes (in Drive, not local)
       - Deleted nodes (in local, not in Drive)
       - Updated nodes (compare modification times)
    """
    service = get_google_drive_service()
    files = await service.list_nodes_on_drive(curriculum_folder_id)

    # Convert to FileMetadata format
    metadata_list = [
        FileMetadata(
            file_id=f["id"],
            name=f["name"],
            modified_time=f.get("modifiedTime"),
        )
        for f in files
    ]

    return ListNodesResponse(
        nodes=metadata_list,
        count=len(metadata_list)
    )


@router.get(
    "/status",
    response_model=SyncStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Google Drive sync status",
    responses={
        200: {"description": "Sync status retrieved"},
        500: {"description": "Failed to get status"},
    }
)
async def get_sync_status() -> SyncStatusResponse:
    """
    Get current Google Drive synchronization status.

    **Returns:**
    - is_authenticated: Whether user is authenticated with Drive
    - last_sync_time: Timestamp of last sync
    - curriculum_folders: Number of synced curriculum folders
    - pending_changes: Number of pending changes to sync

    **Usage:**
    Call periodically to monitor sync status and show UI indicators.
    """
    from backend.app.db.session import SessionLocal
    from backend.app.models.sync_metadata import SyncMetadata, CurriculumDriveFolder

    service = get_google_drive_service()
    db = SessionLocal()

    # Query curriculum folders - count Drive folders that exist
    curriculum_folders_count = db.query(CurriculumDriveFolder).filter(
        CurriculumDriveFolder.google_drive_folder_id.isnot(None)
    ).count()

    # Query pending changes - count syncs with status != 'synced'
    pending_changes_count = db.query(SyncMetadata).filter(
        SyncMetadata.sync_status != 'synced'
    ).count()

    result = SyncStatusResponse(
        is_authenticated=service.credentials is not None,
        curriculum_folders=curriculum_folders_count,
        pending_changes=pending_changes_count,
    )

    db.close()
    return result
