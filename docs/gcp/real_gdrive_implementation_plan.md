# Real Google Drive Integration - Implementation Plan

**Date:** 2025-11-20  
**Objective:** Replace MockGDriveService with real Google Drive API integration

---

## Phase 1: Prerequisites & Setup

### 1.1 GCP Configuration Required
- [ ] Enable Google Drive API in GCP Console
- [ ] Create OAuth 2.0 Client ID (Web application)
- [ ] Add authorized redirect URIs
- [ ] Download client configuration

### 1.2 Environment Variables
Add to `.env`:
```
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_FOLDER_NAME=MATHESIS_LAB_DATA
```

---

## Phase 2: Backend Implementation

### 2.1 Real GDrive Service Implementation
**File:** `backend/app/services/gdrive_service.py`

**Changes:**
1. Create `RealGDriveService` class
2. Implement OAuth2 user authentication flow
3. Implement folder creation with parent support
4. Implement file upload (PDF)
5. Implement file deletion
6. Implement get webview link
7. Add error handling and retry logic

**Key Methods:**
```python
class RealGDriveService(GDriveService):
    def __init__(self, credentials: Credentials):
        self.credentials = credentials
        self.service = build('drive', 'v3', credentials=credentials)
    
    def create_folder(self, name: str, parent_id: Optional[str] = None) -> str:
        # Real implementation using Drive API
        
    def upload_file(self, file_obj: BinaryIO, filename: str, parent_id: Optional[str] = None) -> str:
        # Real implementation using Drive API
        
    def delete_file(self, file_id: str) -> bool:
        # Real implementation using Drive API
        
    def get_webview_link(self, file_id: str) -> str:
        # Real implementation using Drive API
```

### 2.2 Authentication Flow
**New File:** `backend/app/api/v1/endpoints/gdrive_auth.py`

**Endpoints:**
- `GET /api/v1/gdrive/auth/url` - Get OAuth URL
- `POST /api/v1/gdrive/auth/callback` - Handle OAuth callback
- `GET /api/v1/gdrive/auth/status` - Check auth status
- `POST /api/v1/gdrive/auth/disconnect` - Disconnect GDrive

### 2.3 Token Storage
**File:** `backend/app/models/user.py`

**Add fields:**
```python
gdrive_access_token: Optional[str]
gdrive_refresh_token: Optional[str]
gdrive_token_expiry: Optional[datetime]
```

### 2.4 Service Factory
**File:** `backend/app/services/gdrive_service.py`

```python
def get_gdrive_service(user_id: str, db: Session) -> GDriveService:
    """Get GDrive service instance for user"""
    if not settings.GOOGLE_DRIVE_ENABLED:
        return MockGDriveService()
    
    user = get_user(user_id, db)
    if not user.gdrive_access_token:
        raise GoogleDriveAuthException("User not authenticated with GDrive")
    
    credentials = get_user_credentials(user)
    return RealGDriveService(credentials)
```

---

## Phase 3: Frontend Implementation

### 3.1 GDrive Auth UI
**New Component:** `MATHESIS-LAB_FRONT/components/GDriveAuthButton.tsx`

**Features:**
- Show connection status
- "Connect to Google Drive" button
- Disconnect option
- Loading states

### 3.2 Settings Page Update
**File:** `MATHESIS-LAB_FRONT/pages/GCPSettings.tsx`

**Add:**
- GDrive connection section
- Status indicator
- Auth button
- Connected account info

### 3.3 API Service
**File:** `MATHESIS-LAB_FRONT/services/gdrive.ts`

```typescript
export const gdriveService = {
  getAuthUrl: () => api.get('/gdrive/auth/url'),
  handleCallback: (code: string) => api.post('/gdrive/auth/callback', { code }),
  getStatus: () => api.get('/gdrive/auth/status'),
  disconnect: () => api.post('/gdrive/auth/disconnect'),
}
```

---

## Phase 4: Testing Strategy

### 4.1 Backend Tests
1. **Unit Tests:**
   - Test RealGDriveService methods with mocked Drive API
   - Test auth flow
   - Test token refresh

2. **Integration Tests:**
   - Test with real GDrive (using test account)
   - Test folder creation
   - Test file upload
   - Test error scenarios

### 4.2 Frontend Tests
1. **Component Tests:**
   - GDriveAuthButton rendering
   - Auth flow UI

2. **E2E Tests:**
   - Complete auth flow
   - Create curriculum → verify folder in GDrive
   - Upload PDF → verify file in GDrive

### 4.3 Manual Testing Checklist
- [ ] User can connect GDrive account
- [ ] Creating curriculum creates folder in GDrive
- [ ] Creating node creates subfolder
- [ ] Uploading PDF stores file in correct folder
- [ ] Files are accessible via webview link
- [ ] Disconnecting GDrive works correctly
- [ ] Error messages are user-friendly

---

## Phase 5: Migration Strategy

### 5.1 Feature Flag
```python
# settings.py
GOOGLE_DRIVE_ENABLED = os.getenv("GOOGLE_DRIVE_ENABLED", "false").lower() == "true"
```

### 5.2 Gradual Rollout
1. Deploy with `GOOGLE_DRIVE_ENABLED=false` (uses Mock)
2. Test in staging with real GDrive
3. Enable for beta users
4. Full rollout

### 5.3 Backward Compatibility
- Existing data without `gdrive_folder_id` continues to work
- GDrive integration is optional
- Graceful degradation if GDrive unavailable

---

## Phase 6: Error Handling

### 6.1 Common Errors
- **No auth:** Show "Connect to Google Drive" prompt
- **Token expired:** Auto-refresh or prompt re-auth
- **Quota exceeded:** Show friendly error, queue for retry
- **Network error:** Retry with exponential backoff
- **Permission denied:** Check folder permissions

### 6.2 User Feedback
- Loading indicators during GDrive operations
- Success notifications
- Clear error messages
- Retry options

---

## Implementation Order

1. ✅ **DONE:** Mock implementation
2. **NEXT:** Backend - Real GDrive service
3. **THEN:** Backend - Auth endpoints
4. **THEN:** Backend - User token storage
5. **THEN:** Frontend - Auth UI
6. **THEN:** Frontend - Settings page
7. **THEN:** Testing - Unit tests
8. **THEN:** Testing - Integration tests
9. **THEN:** Testing - E2E tests
10. **FINALLY:** Manual verification & deployment

---

## Estimated Timeline

- **Backend Implementation:** 2-3 hours
- **Frontend Implementation:** 1-2 hours
- **Testing:** 2-3 hours
- **Manual Verification:** 1 hour
- **Total:** 6-9 hours

---

## Success Criteria

✅ User can authenticate with Google Drive  
✅ Curriculum creation creates GDrive folder  
✅ Node creation creates GDrive subfolder  
✅ PDF upload stores file in GDrive  
✅ All tests passing (pytest, npm test, E2E)  
✅ Manual verification successful  
✅ Error handling robust  
✅ UI/UX smooth and intuitive  

---

## Next Steps

1. **Confirm GCP setup** - Ensure OAuth credentials are ready
2. **Start implementation** - Begin with RealGDriveService
3. **Iterative testing** - Test each component as it's built
4. **Full integration** - Connect all pieces
5. **Comprehensive testing** - Run all test suites
6. **Manual verification** - Browser testing
7. **Documentation** - Update docs with real implementation details
