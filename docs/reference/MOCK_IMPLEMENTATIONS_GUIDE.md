# Mock Implementations Guide

**Purpose**: Comprehensive documentation of all mock/template code used during Phase 1 and Phase 2 implementation.

**Last Updated**: 2025-11-17
**Status**: Complete - All mocks documented and mapped to real API integration points

---

## Table of Contents

1. [Overview](#overview)
2. [Backend Mock Architecture](#backend-mock-architecture)
3. [Frontend Mock Architecture](#frontend-mock-architecture)
4. [Mock Lifecycle (Unit → Integration → E2E)](#mock-lifecycle-unit--integration--e2e)
5. [Detailed Mock Inventory](#detailed-mock-inventory)
6. [Migration Path: Mocks → Real APIs](#migration-path-mocks--real-apis)
7. [Testing Strategy](#testing-strategy)

---

## Overview

The MATHESIS LAB project uses a **three-tier testing approach** that progressively replaces mocks with real implementations:

### Testing Pyramid
```
                   E2E Tests (Real Servers)
                  /                    \
           Integration Tests         (Real Servers)
          /                   \
    Unit Tests         (Mock Objects)
```

### Current Status (Phase 2 Complete)
- ✅ **Unit Tests (Backend)**: 183/183 passing (using Mock/MagicMock)
- ✅ **Frontend Tests**: 159/168 passing (using vi.mock for services)
- ✅ **E2E Tests**: 21/21 passing (real servers, no mocks)

### What's Mocked vs Real
| Layer | Status | Mock Type | Real Integration |
|-------|--------|-----------|------------------|
| Unit Tests | ✅ Complete | Mock objects, @patch decorators | No actual APIs |
| Integration Tests | ✅ Complete | SQLAlchemy session mocks | Real database |
| E2E Tests | ✅ Complete | No mocks | Real servers (frontend + backend) |

---

## Backend Mock Architecture

### 1. Database Session Mocking (conftest.py)

**Location**: `backend/tests/conftest.py` (lines 35-65)

**Purpose**: Provide isolated database sessions for testing without affecting production data

**Mock Implementation**:
```python
# Fixture creates isolated transaction for each test
@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        # Rollback ALL changes after test completes
        transaction.rollback()
        session.close()
        connection.close()
```

**How It Works**:
1. Each test gets its own database connection
2. Test runs within a transaction
3. After test completes, transaction rolls back
4. Next test starts with clean database state

**Related Tests**:
- All integration tests in `backend/tests/integration/` use this fixture
- Example: `test_curriculum_crud_api.py`, `test_node_crud_api.py`

**When to Remove**: Never - this is test best practice for database isolation

---

### 2. FastAPI TestClient Mocking (conftest.py)

**Location**: `backend/tests/conftest.py` (lines 49-64)

**Purpose**: Override FastAPI's dependency injection to use test database

**Mock Implementation**:
```python
@pytest.fixture(name="client")
def client_fixture(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.expunge_all()

    # Inject mock db_session into FastAPI
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

**How It Works**:
1. Creates TestClient that simulates HTTP requests
2. Overrides FastAPI's `get_db()` dependency
3. All API calls in tests use test database session
4. No real HTTP server needed for integration tests

**Related Tests**:
- All API endpoint tests: `test_curriculum_crud_api.py`, `test_node_content_api.py`, etc.

**When to Remove**: Never - this is FastAPI testing best practice

---

### 3. Google Drive Service Mocking

#### 3.1 OAuth Flow Mocking

**Location**: `backend/tests/unit/test_google_drive_service.py` (lines 58-72)

**Purpose**: Test OAuth authentication without actual Google API calls

**Mock Implementation**:
```python
@patch('backend.app.services.google_drive_service.Flow')
def test_get_auth_url_with_credentials(self, mock_flow_class):
    """Test get_auth_url generates valid authorization URL"""
    mock_flow = MagicMock()
    mock_flow_class.from_client_secrets_info.return_value = mock_flow
    mock_flow.authorization_url.return_value = (
        "https://accounts.google.com/auth",
        "state"
    )

    service = GoogleDriveService()
    service.client_id = "test_client_id"
    service.client_secret = "test_client_secret"

    auth_url = service.get_auth_url("test_state")

    assert "https://accounts.google.com/auth" == auth_url
    mock_flow_class.from_client_secrets_info.assert_called_once()
```

**What's Being Mocked**:
- `google.auth.oauthlib.flow.Flow` - OAuth flow class
- Authentication URL generation
- Token exchange logic

**Related Test Classes**:
- `TestGoogleDriveOAuth` (lines 46-160)

**What's NOT Mocked**:
- Service Account credential file loading (`Path.exists()`)
- OAuth token storage/retrieval

**Migration Strategy**:
- Unit tests will remain with mocks (no need for real Google credentials in CI)
- Integration tests will use Service Account credentials from `.env`
- E2E tests will use real OAuth flow (manual testing only)

#### 3.2 Google Drive CRUD Operations Mocking

**Location**: `backend/tests/unit/test_google_drive_service.py` (lines 130-220)

**Purpose**: Test file upload/download/delete logic without actual Drive API

**Mock Implementation Examples**:

**Create/Upload**:
```python
@patch('backend.app.services.google_drive_service.build')
def test_save_node_to_drive(self, mock_build):
    """Test saving node content to Google Drive"""
    mock_drive_service = MagicMock()
    mock_build.return_value = mock_drive_service

    service = GoogleDriveService(use_service_account=False)
    service.service = mock_drive_service

    # Mock Drive API response
    mock_drive_service.files().create().execute.return_value = {
        'id': 'drive-file-123',
        'name': 'Test Node'
    }

    result = service.save_node_to_drive(
        curriculum_id="curr-123",
        node_id="node-123",
        content="# Node Content"
    )

    assert result['id'] == 'drive-file-123'
```

**Read/Download**:
```python
# Mock file retrieval from Drive
mock_drive_service.files().get().execute.return_value = {
    'id': 'drive-file-123',
    'name': 'Test Node',
    'webContentLink': 'https://drive.google.com/...'
}
```

**Delete**:
```python
# Mock file deletion from Drive
mock_drive_service.files().delete().execute.return_value = None
```

**Related Test Classes**:
- `TestGoogleDriveCRUD` (lines 130-220)
- `TestGoogleDriveError` (lines 221-300)

**Migration Path**:
- Keep unit tests with mocks for CI/CD pipeline
- Create separate `test_google_drive_integration.py` with real Service Account credentials
- Real credentials stored in GitHub Secrets (not in repo)

---

### 4. Sync Service Mocking

**Location**: `backend/tests/unit/test_sync_service.py` (lines 21-48)

**Purpose**: Test synchronization logic without real database or Drive service

**Mock Implementation**:
```python
@pytest.fixture
def mock_db():
    """Create mock database session"""
    return Mock()

@pytest.fixture
def mock_drive_service():
    """Create mock Google Drive service"""
    service = Mock()
    service.save_node_to_drive = AsyncMock()
    service.load_node_from_drive = AsyncMock()
    service.update_node_on_drive = AsyncMock()
    service.delete_node_from_drive = AsyncMock()
    service.list_nodes_on_drive = AsyncMock()
    service.get_file_metadata = AsyncMock()
    return service

@pytest.fixture
def sync_service(mock_db, mock_drive_service):
    """Create SyncService instance with mocks"""
    return SyncService(
        db=mock_db,
        google_drive_service=mock_drive_service,
        conflict_strategy=ConflictResolutionStrategy.LAST_WRITE_WINS,
    )
```

**What's Being Mocked**:
- Database operations (no real SQLAlchemy queries)
- Google Drive service methods (no real API calls)
- Async operations with AsyncMock

**Related Test Classes**:
- `TestSyncServiceInitialization` (lines 50-76)
- `TestSyncUpOperation` (lines 78-180)
- `TestSyncDownOperation` (lines 182-280)
- `TestConflictResolution` (lines 282-400)

**Test Examples**:
```python
@pytest.mark.asyncio
async def test_sync_up_modified_node(self, sync_service, mock_db, mock_drive_service):
    """Test syncing a modified node up to Drive"""
    curriculum_id = "550e8400-e29b-41d4-a716-446655440000"
    folder_id = "drive-folder-123"

    # Create mock node
    node = Mock(spec=Node)
    node.node_id = "node-123"
    node.curriculum_id = curriculum_id
    node.title = "Updated Node"
    node.updated_at = datetime.now(UTC)

    # Simulate sync operation
    sync_service.sync_up_modified_node(curriculum_id, node)

    # Verify Drive service was called correctly
    mock_drive_service.update_node_on_drive.assert_called_once()
```

**Migration Strategy**:
- Unit tests remain with mocks (CI/CD)
- Integration tests use real database + mock Drive service
- Full sync testing requires both real DB and Drive (separate test suite)

---

## Frontend Mock Architecture

### 1. Service Module Mocking (Vitest)

**Location**: All `.test.tsx` files using `vi.mock()`

**Purpose**: Test React components without actual API calls

**Mock Implementation Pattern**:
```typescript
// Example: CreateNodeModal.test.tsx
import * as curriculumService from '../services/curriculumService';

vi.mock('../services/curriculumService', () => ({
    createNode: vi.fn(),
}));

describe('CreateNodeModal Component', () => {
    const mockNewNode = {
        node_id: 'node-456',
        curriculum_id: 'curriculum-123',
        title: 'Test Node',
        // ... mock data
    };

    beforeEach(() => {
        vi.clearAllMocks();
        (curriculumService.createNode as any).mockResolvedValue(mockNewNode);
    });

    it('should create node on form submission', async () => {
        render(<CreateNodeModal ... />);
        // Test component logic without real API
    });
});
```

**Mocked Services**:

| Service | File | Mock Functions | Status |
|---------|------|----------------|--------|
| `curriculumService` | `CreateNodeModal.test.tsx` | `createNode()` | ✅ Complete |
| `gcpService` | `AIAssistant.test.tsx` | `summarizeContent()`, `extendContent()`, `generateManimGuidelines()` | ✅ Complete |

**How Mocking Works**:
1. `vi.mock()` replaces actual service with mock implementation
2. Mock returns predefined response data
3. Component tests verify UI behavior, not API logic
4. `.mockResolvedValue()` simulates successful API response
5. `.mockRejectedValue()` simulates API errors

**When to Update Mocks**:
- When service method signatures change
- When API response structure changes
- When adding new service methods

---

### 2. Component Mocking

**Location**: Various `.test.tsx` files

**Purpose**: Test parent components without rendering complex child components

**Mock Example** (AIAssistant.test.tsx):
```typescript
// Mock Spinner component
vi.mock('./Spinner', () => ({
    default: () => <div data-testid="spinner">Loading...</div>,
}));
```

**Mocked Components**:
- `Spinner` - Loading indicator (simplified to div)
- Any heavy/async child components

---

### 3. React Router and Context Mocking

**Pattern Used**: Wrapper components in test setup

**Example**:
```typescript
// Providers wrapper for components using Router
const renderWithRouter = (component: React.ReactElement) => {
    return render(
        <BrowserRouter>
            {component}
        </BrowserRouter>
    );
};

// Use in tests
renderWithRouter(<ComponentNeedingRouter />);
```

---

## Mock Lifecycle (Unit → Integration → E2E)

### Stage 1: Unit Testing (Mocks Only)

**Backend Example**:
```
Test: test_google_drive_service.py
├── Mocks: @patch decorators for OAuth Flow
├── Mocks: MagicMock for Drive API responses
├── Real: SQLite in-memory database
└── Result: Tests pass without credentials
```

**Frontend Example**:
```
Test: CreateNodeModal.test.tsx
├── Mocks: vi.mock('../services/curriculumService')
├── Real: React Testing Library DOM
└── Result: Tests pass without API server
```

**When to Run**: `npm test` or `pytest backend/tests/unit/`

### Stage 2: Integration Testing (Real DB, Mocked External APIs)

**Backend Example**:
```
Test: test_curriculum_crud_api.py
├── Mocks: Database session (via conftest.py fixture)
├── Real: FastAPI TestClient
├── Real: SQLite database file (test.db)
└── Result: Full API request/response cycle tested
```

**When to Run**: `pytest backend/tests/integration/`

### Stage 3: E2E Testing (Real Servers, No Mocks)

**Example**:
```
Test: e2e/pages/curriculum/curriculum.spec.ts
├── Real: Backend server on port 8000
├── Real: Frontend dev server on port 3002
├── Real: Browser automation with Playwright
└── Result: Full user workflow tested with screenshots
```

**When to Run**: `npm run test:e2e` (after servers started)

**Servers Required**:
```bash
# Terminal 1: Backend
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB \
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Frontend
cd MATHESIS-LAB_FRONT && npm run dev

# Terminal 3: E2E Tests
npm run test:e2e
```

---

## Detailed Mock Inventory

### Backend Mocks Summary

| Component | Location | Mock Type | Fixture/Decorator | Purpose |
|-----------|----------|-----------|------------------|---------|
| Database Session | `conftest.py:35` | Transactional Rollback | `@pytest.fixture` | Isolated test DB |
| FastAPI Client | `conftest.py:49` | Dependency Override | `@pytest.fixture` | HTTP simulation |
| Google OAuth Flow | `test_google_drive_service.py:58` | MagicMock | `@patch` | OAuth without credentials |
| Google Drive API | `test_google_drive_service.py:130` | MagicMock | `@patch` | CRUD without real Drive |
| Database (Sync) | `test_sync_service.py:21` | Mock() | `@pytest.fixture` | Sync logic testing |
| Drive Service (Sync) | `test_sync_service.py:27` | AsyncMock | `@pytest.fixture` | Sync operations |

### Frontend Mocks Summary

| Component | Location | Mock Type | Purpose |
|-----------|----------|-----------|---------|
| Curriculum Service | `CreateNodeModal.test.tsx:8` | `vi.mock()` | Create/read operations |
| GCP Service | `AIAssistant.test.tsx:8` | `vi.mock()` | AI features |
| Spinner Component | `AIAssistant.test.tsx:17` | `vi.mock()` | Loading state |

---

## Migration Path: Mocks → Real APIs

### Phase 1 ✅ (Complete)
**Current State**: All mocks in place, tests passing with mocks

**Tests Running**:
- Backend: 183/183 unit tests (with mocks)
- Frontend: 159/168 component tests (with mocks)
- E2E: 21/21 browser tests (real servers)

### Phase 2 ✅ (Complete)
**Current State**: Google Drive Service implemented, Sync Engine implemented

**What's Implemented**:
- ✅ OAuth 2.0 authentication endpoints
- ✅ Service Account authentication
- ✅ Google Drive CRUD operations
- ✅ Bi-directional synchronization
- ✅ Conflict resolution strategies

**Still Using Mocks**:
- Unit tests for security (credentials not in CI)
- Integration tests for development speed
- E2E tests don't call actual Google Drive (only test page rendering)

### Phase 3 (Next - Real Integration Testing)

**What Needs to Happen**:

1. **Create Real Google Drive Integration Tests**
   ```python
   # New file: backend/tests/integration/test_google_drive_real.py
   # Uses actual Service Account credentials from .env
   # Makes real API calls to Google Drive
   # Tests actual file sync behavior
   ```

2. **Set Up CI/CD with Real Credentials**
   ```yaml
   # GitHub Actions needs:
   # - GOOGLE_SERVICE_ACCOUNT_JSON (secret)
   # - Skip real integration tests by default
   # - Only run with special flag for full testing
   ```

3. **Create OAuth E2E Tests**
   ```typescript
   // New file: e2e/pages/oauth/oauth-flow.spec.ts
   // Tests actual OAuth login flow
   // Requires test Google account
   // Manual testing only (can't automate user login)
   ```

### Phase 4 (Future - Production Ready)

**Remove Mocks**:
- Keep unit test mocks (best practice)
- Replace integration test mocks with real services
- Full E2E coverage with real authentication

**Add Monitoring**:
- Real API call logging
- Error tracking
- Performance monitoring

**Update Docs**:
- Real integration guide
- Troubleshooting for production

---

## Testing Strategy

### Unit Tests (Backend)

**Philosophy**: Test business logic, use mocks for external dependencies

**File Pattern**: `backend/tests/unit/test_*.py`

**Mocking Strategy**:
```python
# Always mock external services
@patch('backend.app.services.google_drive_service.Flow')
def test_oauth_flow(self, mock_flow):
    # Test service logic without real Google API
    pass

# Never mock database in unit tests
# (use fixtures instead)
def test_service_with_db(self, db_session):
    # Real SQLAlchemy operations
    pass
```

**Mock Usage Examples**:
- `@patch` - Replace entire module
- `MagicMock()` - Mock object with spec
- `AsyncMock()` - Mock async functions
- `Mock(spec=ClassName)` - Mock with type safety

**When Tests Pass**:
- Run: `pytest backend/tests/unit/ -v`
- Result: All mocks called correctly
- Does NOT guarantee API integration works

---

### Integration Tests (Backend)

**Philosophy**: Test full request/response cycle, use real database

**File Pattern**: `backend/tests/integration/test_*_api.py`

**Mocking Strategy**:
```python
# Use real FastAPI TestClient
def test_curriculum_crud_api(client):
    # Make actual HTTP requests via TestClient
    response = client.post("/api/v1/curriculums", json={...})
    assert response.status_code == 201

# Use real database transactions
def test_curriculum_crud_api(client, db_session):
    # Verify data persisted to database
    curriculum = db_session.query(Curriculum).first()
    assert curriculum is not None
```

**What's Mocked**: Nothing (except optional external APIs like Google Drive)

**When Tests Pass**:
- Run: `pytest backend/tests/integration/ -v`
- Result: Full API workflow works
- Does NOT guarantee frontend integration works

---

### Component Tests (Frontend)

**Philosophy**: Test React behavior, mock service calls

**File Pattern**: `MATHESIS-LAB_FRONT/**/*.test.tsx`

**Mocking Strategy**:
```typescript
// Mock service modules
vi.mock('../services/curriculumService', () => ({
    createNode: vi.fn(),
}));

// Test component behavior
it('should call createNode when form submitted', async () => {
    const { getByRole } = render(<CreateNodeModal />);

    // User interaction
    fireEvent.click(getByRole('button', { name: /create/i }));

    // Verify service called
    expect(curriculumService.createNode).toHaveBeenCalled();
});
```

**What's Mocked**:
- Service modules (API calls)
- External components (heavy dependencies)
- Browser APIs if needed

**What's Real**:
- React component rendering
- DOM interactions
- React hooks behavior

**When Tests Pass**:
- Run: `npm test`
- Result: Component logic works
- Does NOT guarantee API integration works

---

### E2E Tests (Playwright)

**Philosophy**: Test complete user workflows with real servers

**File Pattern**: `MATHESIS-LAB_FRONT/e2e/**/*.spec.ts`

**Mocking Strategy**: NO MOCKS - Real servers only

```typescript
// Real browser automation
test('should create curriculum and add node', async ({ page }) => {
    // Navigate to real frontend
    await page.goto('http://localhost:3002');

    // Real user interactions
    await page.click('text=Create Curriculum');
    await page.fill('[name=title]', 'Test Curriculum');
    await page.click('text=Create');

    // Verify real backend response
    expect(page.url()).toContain('/curriculum/');
});
```

**Requirements**:
- Frontend server running: `npm run dev` (port 3002)
- Backend server running: `uvicorn ... --port 8000`
- Real database (test.db)

**When Tests Pass**:
- Run: `npm run test:e2e`
- Result: Complete workflow works end-to-end
- Servers must be running for tests to work

---

## Key Mock Patterns

### Pattern 1: MagicMock for Method Chaining

**Problem**: Google Drive API uses method chaining
```python
service.files().create(body={...}).execute()
```

**Solution**: Chain mocks
```python
mock_drive_service = MagicMock()
mock_drive_service.files().create().execute.return_value = {'id': '123'}

# Now this works:
result = mock_drive_service.files().create(body={...}).execute()
assert result['id'] == '123'
```

### Pattern 2: AsyncMock for Async Functions

**Problem**: SyncService uses async/await
```python
async def sync_up(self, curriculum_id):
    await self.drive_service.save_node_to_drive(...)
```

**Solution**: Use AsyncMock
```python
mock_drive_service = Mock()
mock_drive_service.save_node_to_drive = AsyncMock()
mock_drive_service.save_node_to_drive.return_value = True

# Now this works:
await sync_service.sync_up(curriculum_id)
```

### Pattern 3: @patch Decorator for Module Replacement

**Problem**: Want to replace entire Google Flow module

**Solution**: Use @patch
```python
@patch('backend.app.services.google_drive_service.Flow')
def test_oauth(self, mock_flow_class):
    mock_flow = MagicMock()
    mock_flow_class.from_client_secrets_info.return_value = mock_flow
    # Now Flow class is replaced for this test
```

### Pattern 4: Vitest vi.mock() for Module Mocking

**Problem**: Want to replace service in React component test

**Solution**: Use vi.mock() at top of test file
```typescript
vi.mock('../services/curriculumService', () => ({
    createNode: vi.fn(),
}));

// Now all imports of curriculumService get the mock
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Mock Not Being Called

**Problem**:
```python
@patch('module.Function')
def test_something(self, mock_function):
    # Test code...
    # mock_function never gets called
    mock_function.assert_called()  # FAILS
```

**Solution**: Check the path
```python
# Wrong - imports module before patch applies
from module import Function

# Right - patch the path where it's used
@patch('service_module.Function')
def test_something(self, mock_function):
    service = ServiceClass()  # This uses the mocked Function
```

### Pitfall 2: Async Mock Not Awaited

**Problem**:
```python
mock_service.async_method = AsyncMock()
result = mock_service.async_method()  # Returns coroutine, not result
```

**Solution**: Await the call
```python
result = await mock_service.async_method()  # Correct
```

### Pitfall 3: Database Session Not Rolled Back

**Problem**:
```python
def test_create_curriculum(client):
    response = client.post(...)
    # Test passes but DB is dirty

def test_read_curriculum(client):
    # Sees data from previous test!
```

**Solution**: Use fixture with rollback
```python
@pytest.fixture(scope="function")
def db_session():
    # ... create transaction ...
    yield session
    transaction.rollback()  # Clean up
```

---

## Documentation References

**Related Documents**:
- `docs/tdd_unit_test_code.md` - Unit test implementations
- `docs/tdd_test_cases.md` - Test case specifications
- `docs/testing/frontend_testing_strategy.md` - Frontend testing details
- `docs/testing/E2E_TESTS_GUIDE.md` - E2E test guide
- `docs/reference/ENVIRONMENT_SETUP.md` - Environment configuration

**External References**:
- [Pytest Documentation](https://docs.pytest.org/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Vitest Documentation](https://vitest.dev/)
- [Playwright Documentation](https://playwright.dev/)

---

## Summary

### What's Mocked

**Backend**:
- Google OAuth Flow (external dependency)
- Google Drive API (external dependency)
- Sync service dependencies (for unit tests)

**Frontend**:
- API services (external dependency)
- Heavy components (for unit tests)
- Router/Context (for component isolation)

### What's NOT Mocked

**Backend**:
- Database operations (real SQLite)
- Business logic (services)
- API endpoints (real FastAPI)

**Frontend**:
- React rendering (real VDOM)
- Component state (real useState/useReducer)
- DOM interactions (real user events)

**E2E**:
- Nothing - all real

### Key Principles

1. **Unit Tests Use Mocks**: Isolate component logic
2. **Integration Tests Are Real**: Verify full workflow
3. **E2E Tests Are Real**: Verify user experience
4. **Keep Mocks Simple**: Easy to maintain and update
5. **Document Mock Behavior**: Why mock instead of test real?

---

## Next Steps

**For Developers**:
1. Read the mock implementation for the layer you're testing
2. Follow the patterns shown in examples
3. Keep mocks focused and simple
4. Update this guide when adding new mocks

**For QA/Testing**:
1. Run unit tests with `pytest backend/tests/unit/`
2. Run integration tests with `pytest backend/tests/integration/`
3. Run E2E tests with `npm run test:e2e` (after starting servers)
4. Use test reports from `python tools/test_report_generator.py`

**For DevOps/CI-CD**:
1. Unit tests can run without credentials (mocked)
2. Integration tests need test database
3. E2E tests need real servers (run separately)
4. See `docs/reference/REPORT_GENERATION_PIPELINE.md` for automation
