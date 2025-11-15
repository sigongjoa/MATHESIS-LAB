# Software Design Document: GCP Integration

## 1. Introduction

### 1.1 Purpose
This document defines the comprehensive design for integrating Google Cloud Platform (GCP) services into MATHESIS LAB for:
- Multi-device synchronization via Google Drive
- Cloud-based data backup and recovery
- User authentication and authorization
- Cloud-based AI services (Vertex AI/Gemini)

### 1.2 Scope
- Service account setup and management
- Google Drive API integration
- OAuth 2.0 authentication flow
- Data synchronization architecture
- Security and compliance measures

### 1.3 Target Audience
- Backend developers
- DevOps engineers
- Security architects
- QA engineers

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Devices                          │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐    │
│  │ Windows PC  │  │ MacBook Pro  │  │ Android App │    │
│  └──────┬──────┘  └──────┬───────┘  └──────┬──────┘    │
└─────────┼──────────────────┼─────────────────┼───────────┘
          │                  │                 │
          └──────────────────┼─────────────────┘
                             │
                    ┌────────▼────────┐
                    │  React Frontend  │
                    │ (OAuth 2.0 Flow) │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
    │ FastAPI    │   │ Google Cloud │   │   GCP IAM   │
    │ Backend    │◄──┤ (Drive, IAM) │   │             │
    │ (OAuth Val)│   └──────┬───────┘   └─────────────┘
    └─────┬──────┘          │
          │          ┌──────▼──────────┐
          │          │ Google Drive    │
          │          │ (Backup/Sync)   │
          │          └─────────────────┘
    ┌─────▼──────────────┐
    │  SQLite Database   │
    │  (Local + Sync)    │
    └────────────────────┘
```

### 2.2 Component Architecture

```
GCP Integration Layer
├── Authentication Module
│   ├── Service Account Manager
│   ├── OAuth 2.0 Handler
│   ├── Token Manager
│   └── Permission Validator
├── Drive Sync Module
│   ├── File Uploader
│   ├── File Downloader
│   ├── Sync Queue Manager
│   ├── Conflict Resolver
│   └── Change Tracker
├── Cloud Storage Module
│   ├── Bucket Manager
│   ├── File Manager
│   └── ACL Manager
├── Vertex AI Module
│   ├── Model Selector
│   ├── Request Handler
│   └── Response Parser
└── Error Handling
    ├── Exception Logger
    ├── Retry Manager
    └── Fallback Handler
```

---

## 3. Detailed Design

### 3.1 Authentication Design

#### 3.1.1 Service Account Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Backend Server (MATHESIS LAB)                               │
│                                                              │
│ 1. Load service-account-key.json from secure location      │
│ 2. Initialize Google API client                            │
│ 3. Create credentials from service account                 │
│ 4. Request OAuth 2.0 token (scoped permissions)            │
│ 5. Use token for API calls to GCP services                 │
│                                                              │
│ ┌──────────────────┐      ┌─────────────────┐              │
│ │ Service Account  │─────►│ GCP OAuth Token │              │
│ │ Key (JSON file)  │      │ (1 hour validity)               │
│ └──────────────────┘      └────────┬────────┘              │
│                                    │                        │
│                           ┌────────▼─────────┐              │
│                           │ Credential Cache │              │
│                           │ (Refresh before  │              │
│                           │  expiration)     │              │
│                           └──────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
# backend/app/core/gcp_auth.py

from google.oauth2 import service_account
from google.auth.transport.requests import Request
import os
from datetime import datetime, timedelta

class ServiceAccountManager:
    def __init__(self):
        self.key_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/cloud-platform'
        ]
        self.credentials = None
        self.token_expiry = None

    def get_credentials(self):
        """Get valid credentials, refreshing if necessary"""
        if self.credentials and self._is_token_valid():
            return self.credentials

        self.credentials = service_account.Credentials.from_service_account_file(
            self.key_path,
            scopes=self.scopes
        )
        self.token_expiry = datetime.utcnow() + timedelta(hours=1)
        return self.credentials

    def _is_token_valid(self):
        """Check if current token is still valid"""
        if not self.token_expiry:
            return False
        return datetime.utcnow() < self.token_expiry - timedelta(minutes=5)

    def refresh_credentials(self):
        """Force refresh of credentials"""
        if self.credentials:
            request = Request()
            self.credentials.refresh(request)
            self.token_expiry = datetime.utcnow() + timedelta(hours=1)
```

#### 3.1.2 OAuth 2.0 User Flow

```
┌──────────────────────────────────────────────────────────────┐
│ User Device (Frontend)                                       │
│                                                               │
│ 1. User clicks "Sign in with Google"                         │
│ 2. Frontend initiates OAuth flow                             │
│ 3. Redirects to Google OAuth consent screen                  │
│ 4. User authorizes MATHESIS LAB app                          │
│ 5. Google redirects to callback URL with auth code           │
│ 6. Frontend exchanges code for access token                  │
│ 7. Frontend sends token to backend                           │
│ 8. Backend validates and stores token                        │
│                                                               │
│ State Machine:                                               │
│ INIT ──► PENDING_AUTH ──► CODE_RECEIVED ──► TOKEN_OBTAINED   │
│                                                  │             │
│                                          ┌──────▼──────┐      │
│                                          │ TOKEN VALID │      │
│                                          └──────┬──────┘      │
│                                                 │              │
│                                          ┌──────▼──────┐      │
│                                          │ AUTHENTICATED       │
│                                          └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

**Frontend Implementation (React):**

```typescript
// MATHESIS-LAB_FRONT/services/gcp/oauth.ts

import { GoogleOAuthProvider, useGoogleLogin } from '@react-oauth/google';

interface OAuthConfig {
    clientId: string;
    clientSecret: string;
    redirectUri: string;
    scopes: string[];
}

class OAuthManager {
    private config: OAuthConfig;
    private accessToken: string | null = null;
    private refreshToken: string | null = null;
    private tokenExpiry: Date | null = null;

    constructor(config: OAuthConfig) {
        this.config = config;
    }

    /**
     * Initiate OAuth login flow
     */
    async initiateLogin(): Promise<void> {
        const authUrl = this.buildAuthUrl();
        window.location.href = authUrl;
    }

    /**
     * Build OAuth authorization URL
     */
    private buildAuthUrl(): string {
        const params = new URLSearchParams({
            client_id: this.config.clientId,
            redirect_uri: this.config.redirectUri,
            response_type: 'code',
            scope: this.config.scopes.join(' '),
            access_type: 'offline', // For refresh token
            prompt: 'consent'
        });

        return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`;
    }

    /**
     * Handle OAuth callback
     */
    async handleCallback(code: string): Promise<void> {
        // Exchange code for tokens via backend
        const response = await fetch('/api/v1/auth/oauth/callback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code })
        });

        const { accessToken, refreshToken, expiresIn } = await response.json();

        this.accessToken = accessToken;
        this.refreshToken = refreshToken;
        this.tokenExpiry = new Date(Date.now() + expiresIn * 1000);

        // Store tokens securely
        this.storeTokens();
    }

    /**
     * Get valid access token
     */
    async getAccessToken(): Promise<string> {
        if (this.isTokenValid()) {
            return this.accessToken!;
        }

        await this.refreshAccessToken();
        return this.accessToken!;
    }

    /**
     * Check if token is still valid
     */
    private isTokenValid(): boolean {
        if (!this.tokenExpiry) return false;
        return Date.now() < this.tokenExpiry.getTime() - 5 * 60 * 1000; // 5 min buffer
    }

    /**
     * Refresh access token using refresh token
     */
    private async refreshAccessToken(): Promise<void> {
        const response = await fetch('/api/v1/auth/oauth/refresh', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refreshToken: this.refreshToken })
        });

        const { accessToken, expiresIn } = await response.json();

        this.accessToken = accessToken;
        this.tokenExpiry = new Date(Date.now() + expiresIn * 1000);

        this.storeTokens();
    }

    /**
     * Store tokens securely (httpOnly cookies)
     */
    private storeTokens(): void {
        // Store in httpOnly cookie via backend response
        // Frontend should NOT store sensitive tokens in localStorage
    }
}
```

**Backend OAuth Callback Handler:**

```python
# backend/app/api/v1/endpoints/auth.py

from fastapi import APIRouter, HTTPException, Request
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request as GoogleRequest
import httpx
import os

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/oauth/callback")
async def oauth_callback(request: Request, code: str):
    """
    Handle OAuth callback - exchange code for tokens
    """
    try:
        # Exchange code for tokens
        token_response = await _exchange_code_for_tokens(code)

        # Extract tokens
        access_token = token_response['access_token']
        refresh_token = token_response.get('refresh_token')
        expires_in = token_response.get('expires_in', 3600)

        # Get user info using access token
        user_info = await _get_user_info(access_token)

        # Find or create user in database
        user = await _find_or_create_user(user_info)

        # Store tokens securely in database (encrypted)
        await _store_user_tokens(user.id, access_token, refresh_token, expires_in)

        # Return tokens in httpOnly cookies
        response = JSONResponse(
            content={
                "success": True,
                "user_id": user.id,
                "redirect_url": "/curriculum"
            }
        )

        # Set httpOnly, Secure cookies
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=expires_in
        )

        if refresh_token:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=True,
                samesite="Lax",
                max_age=30 * 24 * 60 * 60  # 30 days
            )

        return response

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

async def _exchange_code_for_tokens(code: str) -> dict:
    """Exchange authorization code for tokens"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'https://oauth2.googleapis.com/token',
            data={
                'code': code,
                'client_id': os.getenv('GOOGLE_OAUTH_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_OAUTH_CLIENT_SECRET'),
                'redirect_uri': os.getenv('OAUTH_REDIRECT_URI'),
                'grant_type': 'authorization_code'
            }
        )
        response.raise_for_status()
        return response.json()

async def _get_user_info(access_token: str) -> dict:
    """Get user info from Google"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            'https://www.googleapis.com/oauth2/v2/userinfo',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        response.raise_for_status()
        return response.json()
```

### 3.2 Drive Sync Architecture

#### 3.2.1 Sync Queue Model

```python
# backend/app/models/sync_queue.py

from sqlalchemy import Column, String, JSON, DateTime, Enum
from datetime import datetime
import enum

class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"

class SyncAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SYNC = "sync"

class SyncQueue(Base):
    __tablename__ = "sync_queue"

    sync_id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    device_id = Column(String(36), nullable=False)

    # Sync details
    action = Column(Enum(SyncAction), nullable=False)
    resource_type = Column(String(50), nullable=False)  # 'curriculum', 'node', 'content'
    resource_id = Column(String(36), nullable=False)

    # Payload and status
    payload = Column(JSON, nullable=True)
    status = Column(Enum(SyncStatus), default=SyncStatus.PENDING)
    error_message = Column(String(500), nullable=True)

    # Drive tracking
    drive_file_id = Column(String(255), nullable=True)
    drive_last_modified = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Retry tracking
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(DateTime, nullable=True)
```

#### 3.2.2 Sync Service Architecture

```python
# backend/app/services/sync_service.py

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class SyncService:
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    CONFLICT_RESOLUTION_STRATEGY = 'last_write_wins'  # or 'manual_review'

    def __init__(self, drive_service, db_session):
        self.drive = drive_service
        self.db = db_session

    # ==================== Queue Management ====================

    async def add_to_sync_queue(
        self,
        user_id: str,
        device_id: str,
        action: SyncAction,
        resource_type: str,
        resource_id: str,
        payload: Optional[Dict[str, Any]] = None
    ) -> SyncQueue:
        """
        Add operation to sync queue

        Args:
            user_id: User performing action
            device_id: Source device
            action: CREATE, UPDATE, DELETE, SYNC
            resource_type: curriculum, node, content
            resource_id: ID of resource
            payload: Additional data

        Returns:
            SyncQueue entry
        """
        sync_item = SyncQueue(
            sync_id=generate_uuid(),
            user_id=user_id,
            device_id=device_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload
        )

        self.db.add(sync_item)
        self.db.commit()

        # Trigger async sync
        asyncio.create_task(self.process_sync_queue(user_id))

        return sync_item

    async def process_sync_queue(self, user_id: str) -> None:
        """
        Process all pending sync operations for user

        Algorithm:
        1. Fetch all PENDING items for user
        2. Group by resource_type and resource_id
        3. Detect conflicts
        4. Apply changes in order
        5. Update Drive
        6. Mark completed or failed
        """
        pending_items = self.db.query(SyncQueue).filter(
            SyncQueue.user_id == user_id,
            SyncQueue.status == SyncStatus.PENDING
        ).order_by(SyncQueue.created_at).all()

        for sync_item in pending_items:
            try:
                await self._process_single_sync(sync_item)
            except Exception as e:
                await self._handle_sync_error(sync_item, e)

    # ==================== Sync Operations ====================

    async def _process_single_sync(self, sync_item: SyncQueue) -> None:
        """Process single sync operation"""
        sync_item.status = SyncStatus.IN_PROGRESS
        self.db.commit()

        try:
            if sync_item.action == SyncAction.CREATE:
                await self._handle_create(sync_item)
            elif sync_item.action == SyncAction.UPDATE:
                await self._handle_update(sync_item)
            elif sync_item.action == SyncAction.DELETE:
                await self._handle_delete(sync_item)
            elif sync_item.action == SyncAction.SYNC:
                await self._handle_sync(sync_item)

            sync_item.status = SyncStatus.COMPLETED
            sync_item.completed_at = datetime.utcnow()
            self.db.commit()

        except Exception as e:
            raise e

    async def _handle_create(self, sync_item: SyncQueue) -> None:
        """
        Handle CREATE action:
        1. Verify resource doesn't exist locally
        2. Upload to Drive
        3. Store Drive file ID
        """
        resource = self._get_resource(sync_item.resource_type, sync_item.resource_id)

        if not resource:
            raise ValueError(f"Resource {sync_item.resource_id} not found")

        # Upload to Drive
        drive_file_id = await self._upload_to_drive(
            user_id=sync_item.user_id,
            resource_type=sync_item.resource_type,
            resource_id=sync_item.resource_id,
            data=sync_item.payload or self._serialize_resource(resource)
        )

        sync_item.drive_file_id = drive_file_id
        sync_item.drive_last_modified = datetime.utcnow()

    async def _handle_update(self, sync_item: SyncQueue) -> None:
        """
        Handle UPDATE action:
        1. Check for conflicts with Drive version
        2. Merge if necessary
        3. Update Drive
        4. Update local
        """
        # Get local and remote versions
        local_resource = self._get_resource(sync_item.resource_type, sync_item.resource_id)
        remote_version = await self._get_from_drive(sync_item.drive_file_id)

        # Check for conflicts
        if self._has_conflict(local_resource, remote_version):
            await self._handle_conflict(sync_item, local_resource, remote_version)
        else:
            # No conflict - update Drive
            await self._update_on_drive(
                sync_item.drive_file_id,
                sync_item.payload or self._serialize_resource(local_resource)
            )
            sync_item.drive_last_modified = datetime.utcnow()

    async def _handle_delete(self, sync_item: SyncQueue) -> None:
        """
        Handle DELETE action:
        1. Soft delete locally
        2. Delete from Drive (move to trash)
        3. Mark as deleted
        """
        # Soft delete locally
        resource = self._get_resource(sync_item.resource_type, sync_item.resource_id)
        if resource:
            resource.is_deleted = True
            self.db.commit()

        # Delete from Drive
        if sync_item.drive_file_id:
            await self._delete_from_drive(sync_item.drive_file_id)

    # ==================== Conflict Resolution ====================

    def _has_conflict(self, local: Any, remote: Any) -> bool:
        """
        Detect conflict between local and remote versions

        Conflict Rules:
        - Different last_modified timestamps (within 1 second threshold)
        - Different content hashes
        - Different versions
        """
        local_hash = self._compute_hash(local)
        remote_hash = remote.get('hash')

        return local_hash != remote_hash

    async def _handle_conflict(
        self,
        sync_item: SyncQueue,
        local: Any,
        remote: Dict[str, Any]
    ) -> None:
        """
        Handle conflict between versions

        Strategy: last_write_wins
        """
        if self.CONFLICT_RESOLUTION_STRATEGY == 'last_write_wins':
            local_modified = local.updated_at
            remote_modified = datetime.fromisoformat(remote['updated_at'])

            if local_modified > remote_modified:
                # Local is newer - push to Drive
                await self._update_on_drive(
                    sync_item.drive_file_id,
                    self._serialize_resource(local)
                )
            else:
                # Remote is newer - pull from Drive
                self._update_local_from_remote(sync_item.resource_type, local, remote)

        elif self.CONFLICT_RESOLUTION_STRATEGY == 'manual_review':
            # Mark as conflict, require user intervention
            sync_item.status = SyncStatus.CONFLICT
            sync_item.error_message = "Conflict detected - manual review required"

    # ==================== Drive Operations ====================

    async def _upload_to_drive(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        data: Dict[str, Any]
    ) -> str:
        """Upload resource to Google Drive"""
        folder_id = await self._get_or_create_user_folder(user_id)

        file_metadata = {
            'name': f'{resource_type}_{resource_id}.json',
            'parents': [folder_id],
            'mimeType': 'application/json'
        }

        media = MediaIoBaseUpload(
            io.BytesIO(json.dumps(data).encode()),
            mimetype='application/json'
        )

        file = self.drive.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        return file['id']

    async def _update_on_drive(self, file_id: str, data: Dict[str, Any]) -> None:
        """Update existing file on Drive"""
        media = MediaIoBaseUpload(
            io.BytesIO(json.dumps(data).encode()),
            mimetype='application/json'
        )

        self.drive.files().update(
            fileId=file_id,
            media_body=media
        ).execute()

    async def _get_from_drive(self, file_id: str) -> Dict[str, Any]:
        """Download file from Drive"""
        request = self.drive.files().get_media(fileId=file_id)
        file_content = request.execute()
        return json.loads(file_content.decode())

    async def _delete_from_drive(self, file_id: str) -> None:
        """Move file to trash on Drive"""
        self.drive.files().update(
            fileId=file_id,
            body={'trashed': True}
        ).execute()

    # ==================== Error Handling ====================

    async def _handle_sync_error(self, sync_item: SyncQueue, error: Exception) -> None:
        """Handle sync error with retry logic"""
        sync_item.retry_count += 1
        sync_item.last_retry_at = datetime.utcnow()

        if sync_item.retry_count >= self.MAX_RETRIES:
            sync_item.status = SyncStatus.FAILED
            sync_item.error_message = str(error)
        else:
            sync_item.status = SyncStatus.PENDING
            # Schedule retry
            await asyncio.sleep(self.RETRY_DELAY * sync_item.retry_count)
            await self._process_single_sync(sync_item)

        self.db.commit()

    # ==================== Helper Methods ====================

    def _serialize_resource(self, resource: Any) -> Dict[str, Any]:
        """Convert resource to JSON-serializable dict"""
        return {
            'id': resource.id,
            'type': resource.__class__.__name__,
            'data': resource.to_dict(),
            'hash': self._compute_hash(resource),
            'updated_at': resource.updated_at.isoformat()
        }

    def _compute_hash(self, resource: Any) -> str:
        """Compute hash of resource for conflict detection"""
        import hashlib
        data = json.dumps(self._serialize_resource(resource), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()

    def _get_resource(self, resource_type: str, resource_id: str) -> Optional[Any]:
        """Get resource from database"""
        if resource_type == 'curriculum':
            return self.db.query(Curriculum).filter_by(id=resource_id).first()
        elif resource_type == 'node':
            return self.db.query(Node).filter_by(id=resource_id).first()
        elif resource_type == 'content':
            return self.db.query(NodeContent).filter_by(id=resource_id).first()
        return None
```

---

## 4. API Specifications

### 4.1 Authentication Endpoints

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---|
| POST | `/api/v1/auth/oauth/callback` | Exchange code for tokens | No |
| POST | `/api/v1/auth/oauth/refresh` | Refresh access token | Yes |
| POST | `/api/v1/auth/logout` | Logout user | Yes |
| GET | `/api/v1/auth/user` | Get current user info | Yes |

### 4.2 Sync Endpoints

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---|
| POST | `/api/v1/sync/queue` | Add to sync queue | Yes |
| GET | `/api/v1/sync/queue` | Get sync queue status | Yes |
| POST | `/api/v1/sync/process` | Force process sync queue | Yes |
| GET | `/api/v1/sync/conflicts` | Get unresolved conflicts | Yes |
| POST | `/api/v1/sync/resolve-conflict` | Resolve conflict manually | Yes |

### 4.3 Backup Endpoints

| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---|
| POST | `/api/v1/backup/drive` | Create backup on Drive | Yes |
| GET | `/api/v1/backup/drive` | List Drive backups | Yes |
| POST | `/api/v1/restore/drive/{file_id}` | Restore from backup | Yes |

---

## 5. Database Schema Extensions

### 5.1 New Tables

```sql
-- OAuth Token Storage
CREATE TABLE user_oauth_tokens (
    token_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    expires_at TIMESTAMP NOT NULL,
    scope TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id)
);

-- Device Registration
CREATE TABLE user_devices (
    device_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    device_name VARCHAR(255),
    device_type VARCHAR(50), -- 'web', 'mobile', 'desktop'
    last_sync TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Sync Queue (defined above)

-- Drive File Mapping
CREATE TABLE drive_file_mappings (
    mapping_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(36),
    drive_file_id VARCHAR(255),
    drive_folder_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, resource_id)
);

-- Sync History (audit trail)
CREATE TABLE sync_history (
    history_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    action VARCHAR(50),
    resource_type VARCHAR(50),
    resource_id VARCHAR(36),
    status VARCHAR(20),
    device_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 6. Security Considerations

### 6.1 Authentication Security

**Requirement:** All GCP API calls must use authenticated credentials

**Implementation:**
- Service Account key stored securely (environment variable)
- OAuth tokens stored encrypted in database
- Token expiry enforced
- Automatic token refresh before expiration

### 6.2 Data Protection

**Requirement:** Sensitive data encrypted in transit and at rest

**Implementation:**
- HTTPS only for all API endpoints
- Tokens in httpOnly, Secure cookies
- Database encryption for sensitive fields
- Google Drive provides additional encryption

### 6.3 Access Control

**Requirement:** Users can only access their own data

**Implementation:**
- All API endpoints validate user ownership
- Drive files in user-specific folders
- Database queries filtered by user_id
- Service account has minimal permissions

### 6.4 Audit Logging

**Requirement:** All sync operations logged for compliance

**Implementation:**
- SyncQueue table tracks all operations
- SyncHistory table maintains audit trail
- User device registration tracked
- Failed operations logged with error details

---

## 7. Error Handling and Retry Logic

### 7.1 Error Categories

| Error Type | Cause | Retry | User Impact |
|-----------|-------|-------|-----------|
| Authentication Failure | Invalid credentials | Yes (with refresh) | Redirect to login |
| Network Error | Connection lost | Yes (exponential backoff) | Retry notification |
| Drive Quota Exceeded | API limit reached | Yes (delayed) | Queue message |
| Conflict Detected | Simultaneous edits | No (manual) | Manual resolution |
| File Not Found | Drive file deleted | No | Resync or recreate |

### 7.2 Retry Strategy

```python
# Exponential backoff with jitter
retry_delay = base_delay * (exponential_base ** retry_count) + random_jitter
```

- Base delay: 1 second
- Max retries: 3
- Exponential base: 2
- Max delay: 30 seconds

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Test Areas:**
- Credential management and token refresh
- Sync queue operations
- Conflict detection and resolution
- Error handling and retry logic
- Drive operations (mocked)

### 8.2 Integration Tests

**Test Areas:**
- Full OAuth flow
- End-to-end sync operations
- Multi-device synchronization
- Conflict resolution across devices
- Backup and restore operations

### 8.3 E2E Tests

**Test Scenarios:**
1. User creates curriculum on Device A
2. Device B syncs and receives curriculum
3. User edits on both devices simultaneously
4. Conflicts are detected and resolved
5. Backup is created and can be restored

---

## 9. Deployment and Operations

### 9.1 Pre-Deployment Checklist

- [ ] GCP project created and configured
- [ ] Service account key generated
- [ ] OAuth credentials created
- [ ] Database migrations applied
- [ ] Environment variables configured
- [ ] SSL/TLS certificates valid
- [ ] Rate limiting configured
- [ ] Monitoring and logging enabled

### 9.2 Monitoring and Alerts

**Metrics to monitor:**
- Sync queue size
- Sync failure rate
- API quota usage
- Token refresh failures
- Average sync time
- Conflict resolution rate

---

## 10. Future Enhancements

- [ ] Real-time sync via WebSockets
- [ ] Selective sync (choose which resources to sync)
- [ ] Sync bandwidth optimization
- [ ] Offline mode with automatic sync on reconnect
- [ ] Encryption at rest for sensitive data
- [ ] Multi-cloud support (AWS S3, Azure Blob)

---

## References

- [Google Drive API Documentation](https://developers.google.com/drive/api)
- [OAuth 2.0 Security Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
- [Google Cloud IAM Best Practices](https://cloud.google.com/iam/docs/best-practices)
- [Conflict-free Replicated Data Types (CRDT)](https://crdt.tech/)
