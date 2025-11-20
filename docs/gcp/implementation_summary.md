# Google Drive Structure Sync - Implementation Summary

**Date:** 2025-11-20
**Status:** Mock Implementation Complete

---

## Implementation Overview

Google Drive 구조 동기화 기능이 Mock 서비스를 사용하여 구현되었습니다. 실제 Google Drive API는 나중에 통합할 예정이며, 현재는 개발 및 테스트를 위한 Mock 구현이 완료되었습니다.

---

## Changes Made

### 1. Database Schema Updates

**`backend/app/models/curriculum.py`**
- Added `gdrive_folder_id` column (VARCHAR(255), nullable)

**`backend/app/models/node.py`**
- Added `gdrive_folder_id` column (VARCHAR(255), nullable)

### 2. Mock GDrive Service

**`backend/app/services/gdrive_service.py`**
- Created `GDriveService` abstract base class
- Implemented `MockGDriveService` with fake ID generation
- Methods:
  - `create_folder(name, parent_id)` → returns mock folder ID
  - `upload_file(file_obj, filename, parent_id)` → returns mock file ID
  - `delete_file(file_id)` → logs deletion
  - `get_webview_link(file_id)` → returns mock URL

### 3. Service Layer Integration

**`backend/app/services/curriculum_service.py`**
- Modified `create_curriculum()` to call `gdrive_service.create_folder()`
- Stores returned folder ID in `gdrive_folder_id`

**`backend/app/services/node_service.py`**
- Modified `create_node()` to:
  - Determine parent folder ID (from parent node or curriculum)
  - Call `gdrive_service.create_folder()` with parent ID
  - Store returned folder ID in `gdrive_folder_id`
- Modified `create_pdf_link()` to:
  - Accept `file_obj` (BinaryIO) instead of `drive_file_id`
  - Upload file to Google Drive using `gdrive_service.upload_file()`
  - Store returned file ID in `drive_file_id`

### 4. API Endpoint Updates

**`backend/app/api/v1/endpoints/nodes.py`**
- Modified PDF upload endpoint to accept `UploadFile`
- Changed from accepting `NodeLinkPDFCreate` schema to direct file upload
- Converts uploaded file to BytesIO and passes to service

### 5. Tests

**`backend/tests/services/test_gdrive_structure_sync.py`**
- Test: Curriculum creation creates GDrive folder
- Test: Node creation creates GDrive subfolder
- Test: PDF upload uploads file to GDrive
- Test: Graceful handling when parent folder ID is missing

---

## Current Behavior (Mock)

1. **Create Curriculum "Physics 101"**
   - DB: Curriculum record created
   - Mock GDrive: Logs `[MockGDrive] Creating folder 'Physics 101' -> ID: mock_folder_abc123`
   - DB: `gdrive_folder_id = "mock_folder_abc123"`

2. **Create Node "Newton's Laws" under "Physics 101"**
   - DB: Node record created
   - Mock GDrive: Logs `[MockGDrive] Creating folder 'Newton's Laws' (parent: mock_folder_abc123) -> ID: mock_folder_def456`
   - DB: `gdrive_folder_id = "mock_folder_def456"`

3. **Upload PDF "lecture1.pdf" to "Newton's Laws"**
   - Mock GDrive: Logs `[MockGDrive] Uploading file 'lecture1.pdf' (parent: mock_folder_def456) -> ID: mock_file_ghi789`
   - DB: NodeLink created with `drive_file_id = "mock_file_ghi789"`

---

## Next Steps (Real Implementation)

To integrate with real Google Drive API:

1. **Setup GCP Project**
   - Enable Google Drive API
   - Create OAuth 2.0 credentials or Service Account
   - Download credentials JSON

2. **Implement Real GDrive Service**
   - Create `RealGDriveService` class implementing `GDriveService` interface
   - Use `google-api-python-client` library
   - Implement authentication (OAuth2 or Service Account)

3. **Replace Mock with Real Service**
   ```python
   # In backend/app/services/gdrive_service.py
   # Change:
   gdrive_service = MockGDriveService()
   # To:
   gdrive_service = RealGDriveService(credentials_path="path/to/credentials.json")
   ```

4. **Database Migration**
   - Create Alembic migration to add `gdrive_folder_id` columns
   - Run migration on production database

5. **Testing**
   - Test with real Google Drive account
   - Verify folder/file creation
   - Test error handling (network failures, quota limits, etc.)

---

## Testing the Mock Implementation

```bash
# Run tests
cd backend
pytest tests/services/test_gdrive_structure_sync.py -v
```

Expected output:
```
test_create_curriculum_creates_gdrive_folder PASSED
test_create_node_creates_gdrive_subfolder PASSED
test_upload_pdf_uploads_to_gdrive PASSED
test_node_without_parent_gdrive_folder_skips_upload PASSED
```

---

## API Usage Example

```bash
# 1. Create Curriculum
curl -X POST "http://localhost:8000/api/v1/curriculums/" \
  -H "Content-Type: application/json" \
  -d '{"title": "Physics 101", "description": "Intro to Physics", "is_public": false}'

# Response: {"curriculum_id": "...", "gdrive_folder_id": "mock_folder_...", ...}

# 2. Create Node
curl -X POST "http://localhost:8000/api/v1/nodes/?curriculum_id=<curriculum_id>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Newton'\''s Laws", "node_type": "CHAPTER"}'

# Response: {"node_id": "...", "gdrive_folder_id": "mock_folder_...", ...}

# 3. Upload PDF
curl -X POST "http://localhost:8000/api/v1/nodes/<node_id>/links/pdf" \
  -F "file=@lecture1.pdf"

# Response: {"link_id": "...", "drive_file_id": "mock_file_...", "file_name": "lecture1.pdf", ...}
```

---

## Files Modified/Created

- `backend/app/models/curriculum.py` (modified)
- `backend/app/models/node.py` (modified)
- `backend/app/services/gdrive_service.py` (created)
- `backend/app/services/curriculum_service.py` (modified)
- `backend/app/services/node_service.py` (modified)
- `backend/app/api/v1/endpoints/nodes.py` (modified)
- `backend/tests/services/test_gdrive_structure_sync.py` (created)
- `docs/gcp/sdd_google_drive_structure_sync.md` (created)
- `docs/gcp/tdd_google_drive_structure_sync.md` (created)
- `docs/gcp/implementation_summary.md` (this file)
