# TDD: Google Drive Structure Sync

**Version:** 1.0
**Date:** 2025-11-20
**Status:** Draft

---

## 1. Overview
This document defines the test plan for the Google Drive Structure Sync feature. We will use `pytest` for backend testing and `vitest` for frontend testing (if needed, though most logic is backend).

---

## 2. Backend Test Strategy (Pytest)

### 2.1 Mocks
Since we cannot call the real Google Drive API during unit tests, we will mock the `GDriveService`.

```python
# Mock Object
class MockGDriveService:
    def create_folder(self, name, parent_id=None):
        return f"mock_folder_id_{name}"
    
    def upload_file(self, file, name, parent_id):
        return f"mock_file_id_{name}"
```

### 2.2 Test Cases

#### A. Service Layer Tests (`tests/services/test_curriculum_service.py`)

**Test 1: Create Curriculum triggers Drive Folder Creation**
- **Setup:** Mock `GDriveService`.
- **Action:** Call `create_curriculum(title="Math")`.
- **Assertion:** 
    - Curriculum is saved to DB.
    - `GDriveService.create_folder` was called with "Math".
    - Curriculum record has `gdrive_folder_id` set.

**Test 2: Create Node triggers Drive Sub-folder Creation**
- **Setup:** Existing Curriculum with `gdrive_folder_id="folder_123"`.
- **Action:** Call `create_node(curriculum_id, title="Algebra")`.
- **Assertion:**
    - Node is saved to DB.
    - `GDriveService.create_folder` was called with "Algebra" and `parent_id="folder_123"`.
    - Node record has `gdrive_folder_id` set.

**Test 3: Upload PDF triggers Drive File Upload**
- **Setup:** Existing Node with `gdrive_folder_id="node_folder_456"`.
- **Action:** Call `upload_file_to_node(node_id, file_obj)`.
- **Assertion:**
    - `GDriveService.upload_file` was called.
    - `node_links` record created with `gdrive_file_id`.

#### B. API Endpoint Tests (`tests/api/test_gdrive_sync.py`)

**Test 4: Integration Flow**
- **Scenario:** Create Curriculum -> Create Node -> Upload PDF.
- **Check:** Verify the chain of ID passing works correctly through the API layers.

---

## 3. Frontend Test Strategy (Vitest)

### 3.1 UI Feedback
- **Test:** Verify that the UI shows a "Syncing..." or "Synced" indicator (if implemented).
- **Test:** Verify that clicking a PDF link opens the correct Google Drive viewer URL (if we return the `webViewLink`).

---

## 4. Implementation Steps (TDD Cycle)

1. **Step 1:** Create `GDriveService` interface and Mock.
2. **Step 2:** Write failing test for `create_curriculum` (expecting Drive ID).
3. **Step 3:** Implement `create_curriculum` logic to call `GDriveService`.
4. **Step 4:** Pass test.
5. **Step 5:** Repeat for `create_node` and `upload_pdf`.

