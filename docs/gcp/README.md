# GCP Integration Guide

## Overview

MATHESIS LAB uses Google Cloud Platform (GCP) for:
1. **Cloud Storage** - Store curriculum materials and user files
2. **Google Drive Integration** - Sync and backup curriculum data
3. **Authentication** - OAuth 2.0 for multi-device access
4. **Vertex AI** - AI services (Gemini for content enhancement)

This guide covers GCP setup, authentication, and integration with the MATHESIS LAB backend.

## Table of Contents

1. [GCP Project Setup](#gcp-project-setup)
2. [Authentication Methods](#authentication-methods)
3. [APIs and Services](#apis-and-services)
4. [Security Considerations](#security-considerations)
5. [Implementation Guide](#implementation-guide)

## GCP Project Setup

### Prerequisites
- Google Cloud Account
- Billing enabled
- gcloud CLI installed

### Step 1: Create GCP Project

```bash
# Create new project
gcloud projects create mathesis-lab-project --name="MATHESIS LAB"

# Set as current project
gcloud config set project mathesis-lab-project
```

### Step 2: Enable Required APIs

Required APIs for full functionality:
- Google Drive API
- Cloud Storage API
- Vertex AI API
- Cloud IAM API

```bash
# Enable APIs
gcloud services enable drive.googleapis.com
gcloud services enable storage-api.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable iam.googleapis.com
```

### Step 3: Create Service Account

```bash
# Create service account
gcloud iam service-accounts create mathesis-lab-service \
  --display-name="MATHESIS LAB Service Account"

# Get service account email
gcloud iam service-accounts list --filter="displayName:MATHESIS LAB Service Account"
```

## Authentication Methods

### Method 1: Service Account (Backend/Server)

**Best for:** Server-to-server communication

**Steps:**
1. Create service account (see above)
2. Create and download service account key (JSON)
3. Set environment variable: `GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json`

**Security:** ⭐⭐⭐⭐⭐ (Highest - credentials are server-side only)

```python
# Python example
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'service-account-key.json',
    scopes=['https://www.googleapis.com/auth/drive']
)
```

### Method 2: OAuth 2.0 (Frontend/User)

**Best for:** User authentication and authorization

**Steps:**
1. Create OAuth 2.0 credentials (Web application)
2. Configure authorized redirect URIs
3. Implement OAuth flow in frontend

**Security:** ⭐⭐⭐⭐ (High - user tokens, scoped permissions)

**Required Scopes:**
- `https://www.googleapis.com/auth/drive` - Full Drive access
- `https://www.googleapis.com/auth/drive.file` - Only files created by app
- `https://www.googleapis.com/auth/userinfo.profile` - User profile info

### Method 3: API Key (Limited)

**Best for:** Public APIs only

**Security:** ⭐⭐ (Low - should not be used for sensitive operations)

**Restriction:** Do NOT use for Drive API or sensitive data

## APIs and Services

### Google Drive API

**Purpose:** Backup, sync, and manage curriculum files

**Authentication:** OAuth 2.0 (user) or Service Account (backend)

**Key Operations:**
- Upload curriculum to Drive folder
- Download backups
- Share curriculum with other users
- Version history

```python
# Backend example - upload to Drive
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Build Drive service
drive_service = build('drive', 'v3', credentials=credentials)

# Create folder
folder_metadata = {'name': 'MATHESIS LAB Backups', 'mimeType': 'application/vnd.google-apps.folder'}
folder = drive_service.files().create(body=folder_metadata, fields='id').execute()

# Upload file
file_metadata = {'name': 'curriculum.json', 'parents': [folder['id']]}
media = MediaFileUpload('curriculum.json', mimetype='application/json')
file = drive_service.files().create(body=file_metadata, media_body=media).execute()
```

### Cloud Storage API

**Purpose:** Store large files, media, and backups

**Authentication:** Service Account

**Benefits:**
- Cheaper than Drive for bulk storage
- Better for large files (>100 MB)
- CDN integration for fast delivery

```python
from google.cloud import storage

# Initialize client
storage_client = storage.Client()

# Create bucket
bucket = storage_client.bucket('mathesis-lab-storage')
bucket.storage_class = 'STANDARD'
bucket = storage_client.create_bucket(bucket)

# Upload file
blob = bucket.blob('curriculum_data.json')
blob.upload_from_filename('curriculum_data.json')
```

### Vertex AI API

**Purpose:** AI services (Gemini for content enhancement)

**Authentication:** Service Account

**Current Status:** Integrated in `backend/app/core/genai_config.py`

```python
import vertexai
from vertexai.generative_models import GenerativeModel

# Initialize Vertex AI
vertexai.init(project="mathesis-lab-project", location="us-central1")

# Use Gemini model
model = GenerativeModel("gemini-1.5-flash")
response = model.generate_content("Summarize this curriculum...")
```

## Security Considerations

### 1. Credential Management

**DO:**
- Store credentials in `.env` files (gitignored)
- Use service accounts for backend operations
- Rotate credentials regularly
- Use separate service accounts per environment (dev/prod)

**DON'T:**
- Commit credentials to git
- Use API keys for sensitive operations
- Share credentials across projects
- Use old/deprecated authentication methods

### 2. API Quotas and Rate Limiting

**Drive API:**
- Default quota: 100M requests/day per user
- Rate limit: 1000 queries/100 seconds

**Cloud Storage:**
- No strict rate limit for storage operations
- Monitor costs (storage + egress fees)

### 3. OAuth Consent Screen

**Setup required for user-facing OAuth:**
1. Configure OAuth consent screen (Google Cloud Console)
2. Add scopes (Drive, user profile)
3. Add test users during development
4. Publish for production (requires review)

### 4. Firewall and Access Control

**Recommended:**
- Enable Cloud Armor for DDoS protection
- Use Cloud IAM roles (principle of least privilege)
- Set bucket policies to private by default
- Enable audit logging for all GCP resources

## Implementation Guide

### Phase 1: Service Account Setup (Week 1-2)

**Tasks:**
1. Create GCP project and service account
2. Download service account key
3. Store key in backend `.env`
4. Test basic authentication

**Testing:**
```bash
# Test authentication
python -c "from google.cloud import storage; print('Auth OK')"
```

### Phase 2: Drive Integration (Week 2-3)

**Tasks:**
1. Implement backup to Drive endpoint
2. Implement restore from Drive endpoint
3. Create Drive folder structure
4. Add file versioning

**Endpoints to Create:**
- `POST /api/v1/backup/drive` - Backup curriculum to Drive
- `GET /api/v1/backup/drive` - List Drive backups
- `POST /api/v1/restore/drive/{file_id}` - Restore from Drive

### Phase 3: OAuth Integration (Week 3-4)

**Tasks:**
1. Create OAuth credentials in GCP Console
2. Implement OAuth flow in frontend
3. Store user tokens in database
4. Implement token refresh logic

**Frontend Integration:**
- Use `@react-oauth/google` or `google-auth-library-react`
- Handle token refresh automatically
- Store tokens securely (httpOnly cookies)

### Phase 4: Multi-Device Sync (Week 4-5)

**Tasks:**
1. Implement device registration
2. Create sync queue in backend
3. Implement conflict resolution
4. Test across multiple devices

**Database Schema:**
```sql
-- Device registration
CREATE TABLE user_devices (
    device_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    device_name VARCHAR(255),
    last_sync TIMESTAMP,
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Sync queue
CREATE TABLE sync_queue (
    sync_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    device_id VARCHAR(36) NOT NULL,
    action VARCHAR(50), -- 'create', 'update', 'delete'
    resource_type VARCHAR(50), -- 'curriculum', 'node'
    resource_id VARCHAR(36),
    payload JSON,
    status VARCHAR(20), -- 'pending', 'completed', 'failed'
    created_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

## Environment Variables

```bash
# GCP Configuration
GCP_PROJECT_ID=mathesis-lab-project
GCP_SERVICE_ACCOUNT_KEY=/path/to/service-account-key.json
GOOGLE_APPLICATION_CREDENTIALS=${GCP_SERVICE_ACCOUNT_KEY}

# Drive Configuration
GOOGLE_DRIVE_FOLDER_ID=<backup_folder_id>

# OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID=<client_id>
GOOGLE_OAUTH_CLIENT_SECRET=<client_secret>
OAUTH_REDIRECT_URI=http://localhost:3002/auth/callback

# Vertex AI Configuration
VERTEX_AI_PROJECT_ID=mathesis-lab-project
VERTEX_AI_LOCATION=us-central1
```

## Common Errors and Solutions

### Error: "Permission denied"
- Check service account has necessary IAM roles
- Verify credentials file path is correct
- Ensure API is enabled in GCP Console

### Error: "OAuth redirect_uri mismatch"
- Add correct redirect URI to OAuth credentials in GCP Console
- Ensure frontend URL matches exactly (including protocol and port)

### Error: "Drive quota exceeded"
- Check account quota in GCP Console
- Implement quota monitoring and alerts
- Consider Cloud Storage for large files

## References

- [Google Cloud Documentation](https://cloud.google.com/docs)
- [Google Drive API Documentation](https://developers.google.com/drive/api)
- [Vertex AI Documentation](https://cloud.google.com/vertex-ai/docs)
- [OAuth 2.0 Best Practices](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)

## Next Steps

1. Create GCP project and service account
2. Test Drive API integration
3. Implement OAuth flow in frontend
4. Set up multi-device sync
5. Deploy to production with proper security measures
