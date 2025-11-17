# Mock Inventory - Quick Reference

**Last Updated**: 2025-11-17

Quick lookup table for all mocks used in the codebase. Use this to quickly find where a specific mock is implemented and how to use it.

---

## Backend Mocks

### Database & ORM Mocks

| Mock | Location | Type | Used In | Purpose |
|------|----------|------|---------|---------|
| `db_session` | `backend/tests/conftest.py:35` | Pytest Fixture | All unit tests | Isolated database session with rollback |
| `TestClient` | `backend/tests/conftest.py:49` | Pytest Fixture | All integration tests | HTTP client for testing FastAPI endpoints |
| `get_db` override | `backend/tests/conftest.py:49` | Dependency Override | All API tests | Inject test database into FastAPI |
| `create_engine` | `backend/tests/conftest.py:19` | Real SQLite | All tests | Actual in-memory SQLite (not mocked) |

**How to Use**:
```python
# In test function
def test_something(db_session):
    # db_session is isolated, will rollback after test
    curriculum = Curriculum(title="Test")
    db_session.add(curriculum)
    db_session.commit()
    # Automatically rolls back after test

def test_api(client):
    # client simulates HTTP requests
    response = client.post("/api/v1/curriculums", json={...})
    assert response.status_code == 201
```

---

### Google Drive Service Mocks

#### OAuth & Authentication

| Mock | Location | Decorator | Return Value | Purpose |
|------|----------|-----------|--------------|---------|
| `Flow` class | `test_google_drive_service.py:58` | `@patch('...Flow')` | MagicMock | Google OAuth flow class |
| `Flow.from_client_secrets_info` | `test_google_drive_service.py:61` | Chain mock | MagicMock | Create flow from OAuth credentials |
| `Flow.authorization_url` | `test_google_drive_service.py:63` | Chain mock | `(url, state)` tuple | Generate OAuth authorization URL |
| `Flow.fetch_token` | `test_google_drive_service.py:76` | Chain mock | Token dict | Exchange code for token |
| `Service Account Path.exists()` | `test_google_drive_service.py:24` | `@patch('...Path')` | Boolean | Check if credentials file exists |

**How to Use**:
```python
@patch('backend.app.services.google_drive_service.Flow')
def test_oauth(self, mock_flow_class):
    mock_flow = MagicMock()
    mock_flow_class.from_client_secrets_info.return_value = mock_flow
    mock_flow.authorization_url.return_value = ("https://...", "state")

    service = GoogleDriveService()
    url = service.get_auth_url("state")
    assert "https://" in url
```

#### File Operations (CRUD)

| Mock | Location | Decorator | Purpose |
|------|----------|-----------|---------|
| `build()` function | `test_google_drive_service.py:130` | `@patch('...build')` | Create Google Drive service instance |
| `drive_service.files().create()` | `test_google_drive_service.py:145` | Chain mock | Mock upload file to Drive |
| `drive_service.files().get()` | `test_google_drive_service.py:160` | Chain mock | Mock download file metadata |
| `drive_service.files().update()` | `test_google_drive_service.py:175` | Chain mock | Mock update file on Drive |
| `drive_service.files().delete()` | `test_google_drive_service.py:190` | Chain mock | Mock delete file from Drive |
| `drive_service.files().list()` | `test_google_drive_service.py:205` | Chain mock | Mock list files on Drive |

**How to Use**:
```python
@patch('backend.app.services.google_drive_service.build')
def test_upload(self, mock_build):
    mock_drive = MagicMock()
    mock_build.return_value = mock_drive

    # Mock the API response
    mock_drive.files().create().execute.return_value = {
        'id': 'drive-file-123',
        'name': 'Test File'
    }

    service = GoogleDriveService()
    service.service = mock_drive

    result = service.save_node_to_drive("curr-1", "node-1", "content")
    assert result['id'] == 'drive-file-123'
```

---

### Sync Service Mocks

| Mock | Location | Type | Purpose |
|------|----------|------|---------|
| `mock_db` | `test_sync_service.py:21` | `Mock()` fixture | Mock database session |
| `mock_drive_service` | `test_sync_service.py:27` | `Mock()` + `AsyncMock` fixture | Mock Google Drive service |
| `Node` | `test_sync_service.py:88` | `Mock(spec=Node)` | Mock Node model instance |
| `SyncMetadata` | `test_sync_service.py:97` | `Mock(spec=SyncMetadata)` | Mock sync metadata |

**How to Use**:
```python
@pytest.fixture
def mock_drive_service():
    service = Mock()
    service.save_node_to_drive = AsyncMock()
    service.load_node_from_drive = AsyncMock()
    return service

async def test_sync(sync_service, mock_drive_service):
    mock_drive_service.save_node_to_drive.return_value = {'id': 'file-1'}

    result = await sync_service.sync_up(curriculum_id)

    mock_drive_service.save_node_to_drive.assert_called()
```

---

## Frontend Mocks

### Service Module Mocks

| Service | Test File | Mocked Functions | Status |
|---------|-----------|------------------|--------|
| `curriculumService` | `CreateNodeModal.test.tsx` | `createNode()` | ✅ Complete |
| `gcpService` | `AIAssistant.test.tsx` | `summarizeContent()`, `extendContent()`, `generateManimGuidelines()` | ✅ Complete |

**How to Use**:
```typescript
import * as curriculumService from '../services/curriculumService';

vi.mock('../services/curriculumService', () => ({
    createNode: vi.fn(),
}));

describe('CreateNodeModal', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        (curriculumService.createNode as any).mockResolvedValue({
            node_id: 'node-123',
            title: 'Test'
        });
    });

    it('should create node', async () => {
        // Test uses mocked createNode
        render(<CreateNodeModal ... />);
        // ... assertions ...
    });
});
```

---

### Component Mocks

| Component | Test File | Mock Type | Purpose |
|-----------|-----------|-----------|---------|
| `Spinner` | `AIAssistant.test.tsx` | `vi.mock()` | Simplify loading state |

**How to Use**:
```typescript
vi.mock('./Spinner', () => ({
    default: () => <div data-testid="spinner">Loading...</div>,
}));

// Parent component using Spinner will get the mock version
```

---

### Router/Provider Mocks

**Pattern**: Wrapper component for test setup

| Provider | Usage | Purpose |
|----------|-------|---------|
| `BrowserRouter` | Wrap component in test | Enable React Router |
| `Provider` (Redux) | Wrap component in test | Enable Redux state |
| `QueryClientProvider` | Wrap component in test | Enable React Query |

**How to Use**:
```typescript
const renderWithRouter = (component: React.ReactElement) => {
    return render(
        <BrowserRouter>
            {component}
        </BrowserRouter>
    );
};

// In test
renderWithRouter(<MyComponent />);
```

---

## Test File Organization

### Backend Test Files

```
backend/tests/
├── conftest.py                          # Global fixtures
│   ├── db_session fixture
│   └── client fixture
├── unit/
│   ├── test_google_drive_service.py     # Google Drive mocks
│   ├── test_sync_service.py             # Sync service mocks
│   ├── test_curriculum_service.py       # Service logic
│   └── test_node_service.py             # Service logic
└── integration/
    ├── test_curriculum_crud_api.py      # Real API + real DB
    ├── test_node_content_api.py         # Real API + real DB
    ├── test_oauth_endpoints.py          # Real API + mock OAuth
    └── test_gcp_sync_api.py             # Real API + mock Drive
```

### Frontend Test Files

```
MATHESIS-LAB_FRONT/
├── components/
│   ├── CreateNodeModal.test.tsx         # Mocks curriculumService
│   ├── AIAssistant.test.tsx             # Mocks gcpService
│   ├── BackupManager.test.tsx           # Mocks services
│   └── ...
├── pages/
│   ├── NodeEditor.test.tsx              # Mocks services + Router
│   └── ...
└── e2e/
    ├── pages/
    │   ├── curriculum/
    │   │   └── curriculum.spec.ts       # NO MOCKS - Real servers
    │   └── gcp-settings/
    │       └── gcp-settings.spec.ts     # NO MOCKS - Real servers
    └── ...
```

---

## Mock Usage by Layer

### Unit Test Layer

**What to Mock**:
- External services (Google Drive, OAuth)
- Database operations (sync service unit tests)
- Network calls
- File system access

**What NOT to Mock**:
- Business logic (services)
- Models
- Utilities

**Example**:
```python
@patch('backend.app.services.google_drive_service.Flow')
def test_unit_level(mock_flow):
    # Test service logic with mocked dependency
    service = GoogleDriveService()
    # ...
```

### Integration Test Layer

**What to Mock**:
- Optional: External services (Google Drive for speed)
- Nothing else

**What NOT to Mock**:
- Database (use real SQLite)
- API endpoints (use real FastAPI)
- Business logic

**Example**:
```python
def test_integration_level(client, db_session):
    # Real API + real database
    response = client.post("/api/v1/curriculums", json={...})
    curriculum = db_session.query(Curriculum).first()
    assert curriculum is not None
```

### E2E Test Layer

**What to Mock**:
- Nothing!

**Example**:
```typescript
test('should create curriculum', async ({ page }) => {
    // Real browser + real servers
    await page.goto('http://localhost:3002');
    // Real user interactions
    // Real API calls
    // Real database updates
});
```

---

## Mocking Patterns

### Pattern 1: Simple Mock Function

```python
# Backend
mock_function = Mock()
mock_function.return_value = "result"

# Frontend
vi.fn().mockResolvedValue("result")
```

### Pattern 2: Chain Mocking (Method Chaining)

```python
# Google Drive: service.files().create().execute()
mock_service = MagicMock()
mock_service.files().create().execute.return_value = {'id': '123'}

# Alternative:
mock_service.files.return_value.create.return_value.execute.return_value = {'id': '123'}
```

### Pattern 3: Async Mocking

```python
# Backend
mock_async = AsyncMock()
mock_async.return_value = "result"
await mock_async()  # Returns "result"

# Frontend
vi.fn().mockResolvedValue("result")
// No need for async/await in mock setup
```

### Pattern 4: Patch Decorator

```python
@patch('module.path.ClassName')
def test_something(mock_class):
    mock_class.return_value = MagicMock()
    # All instances use the mock
```

### Pattern 5: Context Manager Patching

```python
with patch('module.Function') as mock_func:
    mock_func.return_value = "result"
    # Test code here
    mock_func.assert_called()
```

---

## Verification Methods

### Backend Verification

```python
# Verify called
mock.assert_called()
mock.assert_called_once()
mock.assert_called_with(arg1, arg2)
mock.assert_called_once_with(arg1, arg2)

# Verify not called
mock.assert_not_called()

# Verify call count
assert mock.call_count == 3

# Verify call arguments
assert mock.call_args == call(arg1, arg2)
```

### Frontend Verification

```typescript
// Verify called
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledTimes(1);
expect(mockFn).toHaveBeenCalledWith(arg1, arg2);
expect(mockFn).toHaveBeenCalledOnce();

// Verify not called
expect(mockFn).not.toHaveBeenCalled();
```

---

## Common Mock Scenarios

### Scenario 1: Test OAuth Without Credentials

**Goal**: Test OAuth flow without real Google credentials

**Solution**:
```python
@patch('backend.app.services.google_drive_service.Flow')
def test_oauth_flow(self, mock_flow_class):
    # Mock the entire Flow class
    mock_flow = MagicMock()
    mock_flow_class.from_client_secrets_info.return_value = mock_flow

    # Run test without credentials
    service = GoogleDriveService()
    url = service.get_auth_url("state")

    # Verify flow was created
    mock_flow_class.from_client_secrets_info.assert_called_once()
```

### Scenario 2: Test Sync Logic Without Drive API

**Goal**: Test sync algorithm without making Drive API calls

**Solution**:
```python
@pytest.fixture
def sync_service(mock_db, mock_drive_service):
    return SyncService(db=mock_db, google_drive_service=mock_drive_service)

async def test_sync_algorithm(sync_service, mock_drive_service):
    # Mock Drive responses
    mock_drive_service.save_node_to_drive = AsyncMock(return_value={'id': 'file-1'})

    # Test sync logic
    await sync_service.sync_up(curriculum_id)

    # Verify correct Drive calls were made
    mock_drive_service.save_node_to_drive.assert_called()
```

### Scenario 3: Test Component Without API Server

**Goal**: Test React component without backend running

**Solution**:
```typescript
vi.mock('../services/curriculumService', () => ({
    createNode: vi.fn().mockResolvedValue({ node_id: 'node-1' }),
}));

it('should handle node creation', async () => {
    // Component tests run without backend
    render(<CreateNodeModal ... />);

    // Mock service is used instead of real API
});
```

---

## Troubleshooting

### Mock Not Being Called

**Problem**: `mock.assert_called()` fails

**Solution**: Check import path
```python
# Wrong path
@patch('google_drive_service.Flow')  # Won't work

# Right path
@patch('backend.app.services.google_drive_service.Flow')  # Works
```

### Async Not Awaited

**Problem**: Async mock returns coroutine instead of value

**Solution**: Await or use AsyncMock
```python
# Wrong
mock_result = mock_async_function()  # Coroutine object

# Right
mock_result = await mock_async_function()  # Actual result

# Or use AsyncMock
mock_async = AsyncMock(return_value="result")
result = await mock_async()  # Works
```

### Mock Not Clearing Between Tests

**Problem**: Previous test's mock state affects next test

**Solution**: Clear mocks in beforeEach/beforeAll
```python
def test_1(self):
    mock.return_value = "value1"
    # test...

def test_2(self):
    mock.reset_mock()  # Clear previous state
    mock.return_value = "value2"
    # test...
```

**Or**:
```typescript
beforeEach(() => {
    vi.clearAllMocks();
});
```

---

## References

- **Main Guide**: `docs/reference/MOCK_IMPLEMENTATIONS_GUIDE.md`
- **Unit Tests**: `backend/tests/unit/`
- **Integration Tests**: `backend/tests/integration/`
- **Component Tests**: `MATHESIS-LAB_FRONT/**/*.test.tsx`
- **E2E Tests**: `MATHESIS-LAB_FRONT/e2e/**/*.spec.ts`
