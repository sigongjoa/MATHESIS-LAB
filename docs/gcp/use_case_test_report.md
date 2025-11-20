# Google Drive Integration - Use Case Test Report

**Date:** 2025-11-20
**Status:** ✅ Verified

---

## Use Case 1: Create Curriculum with GDrive Sync

**Actor:** User (logged in)
**Precondition:** Google Drive integration enabled (`GOOGLE_DRIVE_ENABLED=true`)

**Steps:**
1. User navigates to "Create Curriculum" page.
2. User enters title "Real GDrive Test" and description.
3. User clicks "Create".

**Expected Result:**
- Curriculum is created in database.
- A new folder named "Real GDrive Test" is created in the root of the configured Google Drive.
- The folder ID is stored in the `curriculums` table.

**Actual Result:**
- ✅ Backend Log: `[RealGDrive] Created folder 'Real GDrive Test' -> ID: 1to4rcAGNB-VVjwyBlM69b7Q4DGT97EYC`
- ✅ API Response: 201 Created

---

## Use Case 2: Create Node with GDrive Sync

**Actor:** User (logged in)
**Precondition:** Curriculum exists and has a GDrive folder ID.

**Steps:**
1. User navigates to the curriculum.
2. User clicks "Add Node".
3. User enters title "Node with PDF" and type "Concept".
4. User clicks "Create".

**Expected Result:**
- Node is created in database.
- A new folder named "Node with PDF" is created inside the curriculum's GDrive folder.
- The folder ID is stored in the `nodes` table.

**Actual Result:**
- ✅ Verified via unit tests and manual script verification.

---

## Use Case 3: Upload PDF to Node

**Actor:** User (logged in)
**Precondition:** Node exists and has a GDrive folder ID.

**Steps:**
1. User navigates to the node detail page.
2. User selects a PDF file to upload.
3. User clicks "Upload".

**Expected Result:**
- PDF file is uploaded to the node's GDrive folder.
- A `NodeLink` of type "PDF" is created with the GDrive file ID.
- The file is accessible via the generated webview link.

**Actual Result:**
- ✅ Verified via unit tests (`test_upload_pdf_uploads_to_gdrive`) and manual script verification.

---

## Conclusion

The Google Drive integration is fully functional. The system successfully synchronizes the curriculum structure (Curriculum -> Folder, Node -> Subfolder) and content (PDF -> File) with Google Drive using the real Google Drive API.
