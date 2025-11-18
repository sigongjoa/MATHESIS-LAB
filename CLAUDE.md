# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MATHESIS LAB is an educational platform for creating and managing curriculum maps with AI-assisted features. The project follows SDD (Software Design Document) + TDD (Test-Driven Development) methodology.

**Stack:**
- Backend: FastAPI (Python) with SQLAlchemy ORM, SQLite database
- Frontend: React 19 + TypeScript + Vite
- AI: Google Vertex AI (Gemini) - **Currently NOT in use**
- External APIs: Zotero (literature management), YouTube Data API - **Currently NOT in use**

## Architecture

The codebase is organized as a monorepo with separate backend and frontend:

```
backend/
  app/
    api/v1/endpoints/  # API route handlers (curriculums, nodes, literature, youtube)
    core/              # Configuration and AI integration
    db/                # Database session management
    models/            # SQLAlchemy models (Curriculum, Node, ZoteroItem, YouTubeVideo)
    schemas/           # Pydantic schemas for request/response validation
    services/          # Business logic layer (CurriculumService, NodeService)
  tests/
    unit/              # Unit tests for services and models
    integration/       # API integration tests
    conftest.py        # Pytest fixtures (db_session, client)

MATHESIS-LAB_FRONT/  # React frontend (git submodule)
  components/         # React components
  pages/              # Page components
  services/           # API client services
  types.ts            # TypeScript type definitions

docs/                 # SDD documentation (SRS, SAD, DB design, API specs)
```

## Virtual Environment Policy

**CRITICAL: Always Use Virtual Environment**

Before running ANY backend commands (tests, server, database operations), you MUST activate the virtual environment:

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify activation (should show .venv path)
which python
echo $VIRTUAL_ENV
```

**Never run backend commands without activating .venv first.** This ensures:
- Correct dependencies are loaded
- Tests run with proper package versions
- No conflicts with system Python packages

If `.venv` doesn't exist, create it:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt  # If requirements.txt exists
```

## Common Commands

### Backend Development

**ALWAYS activate virtual environment first:**
```bash
source .venv/bin/activate
```

**Run the development server:**
```bash
cd backend
python -m backend.app.main
# Or: uvicorn backend.app.main:app --reload
```

**Run tests:**
```bash
# All tests (with PYTHONPATH)
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest

# Unit tests only
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest backend/tests/unit/

# Integration tests only
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest backend/tests/integration/

# Specific test file
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest backend/tests/integration/test_curriculum_crud_api.py

# With verbose output
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest -v

# With coverage
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest --cov=backend/app
```

**Database:**
- SQLite file: `mathesis_lab.db` (created automatically on startup via `create_tables()` in `main.py`)
- Test database: `test.db` (file-based, managed by pytest fixtures)
- Tables are auto-created via SQLAlchemy metadata on app startup

### Frontend Development

**Setup and run:**
```bash
cd MATHESIS-LAB_FRONT
npm install
npm run dev
```

**Build:**
```bash
npm run build
```

**Test:**
```bash
npm test
```

**Environment Setup:**
Frontend requires `.env.local` file with:
```
VITE_API_URL=/api/v1
# Note: GEMINI_API_KEY no longer needed - AI features now use backend API
```

**Project Structure:**
```
MATHESIS-LAB_FRONT/
  components/           # React components (CreateNodeModal, AIAssistant, etc.)
  pages/               # Page components (CurriculumEditor, NodeEditor, BrowseCurriculums, etc.)
  services/            # API client services
    - curriculumService.ts   # Curriculum CRUD operations
    - nodeService.ts         # Node link management (Zotero, YouTube)
    - geminiService.ts       # ⚠️ NEEDS REFACTORING - should call backend API
  types.ts             # TypeScript type definitions
  constants.ts         # Application constants
```

## Key Development Patterns

### Backend Testing Strategy

**Test fixtures (conftest.py):**
- `db_session`: Provides isolated database session per test (creates tables before, drops after)
- `client`: FastAPI TestClient with dependency override for `get_db()`

**Writing new tests:**
1. Use `db_session` fixture for direct database operations (unit tests)
2. Use `client` fixture for API endpoint testing (integration tests)
3. Tests automatically rollback after each test to ensure isolation

**Service layer pattern:**
- All business logic lives in `services/` (e.g., `CurriculumService`, `NodeService`)
- Endpoints are thin wrappers that call service methods
- Services are dependency-injected via FastAPI `Depends()`

### API Structure

All API endpoints follow `/api/v1/<resource>` pattern:
- `/api/v1/curriculums` - Curriculum CRUD operations
- `/api/v1/nodes` - Node management (AI features NOT currently active)
- `/api/v1/literature` - Zotero integration (NOT currently active)
- `/api/v1/youtube` - YouTube video info retrieval (NOT currently active)

### Configuration

Environment variables are managed via Pydantic Settings (`backend/app/core/config.py`):
- `DATABASE_URL` - Database connection string
- `VERTEX_AI_PROJECT_ID`, `VERTEX_AI_LOCATION` - GCP AI configuration (NOT currently in use)
- `ENABLE_AI_FEATURES` - Toggle AI features on/off (Currently set to False)
- `ZOTERO_API_BASE_URL`, `ZOTERO_API_KEY` - Zotero integration (NOT currently in use)
- `YOUTUBE_API_KEY` - YouTube Data API (NOT currently in use)

Create a `.env` file in the backend directory to override defaults.

**Note:** Focus development on core curriculum and node management features. External integrations (AI, Zotero, YouTube) are planned for future phases.

## AI Features Status

### Current State (Phase 2)

**AI features are EXPLICITLY DISABLED** in the current phase. This is intentional and documented:

```python
# backend/app/core/config.py
ENABLE_AI_FEATURES: bool = False  # AI features are NOT active
```

**Why Disabled:**
1. Focus on core curriculum and node management CRUD operations
2. AI-powered text summarization, expansion, and Manim generation deferred to Phase 3+
3. Vertex AI Gemini integration planned but not yet implemented
4. Frontend AI components exist but are non-functional stubs

### Disabled AI Features

The following features are **NOT CURRENTLY ACTIVE** but have placeholder implementations:

**Backend (Non-functional):**
- `/api/v1/nodes/{nodeId}/content/summarize` - AI text summarization (stub endpoint, returns empty)
- `/api/v1/nodes/{nodeId}/content/extend` - AI text expansion (stub endpoint, returns empty)
- `/api/v1/nodes/{nodeId}/content/manim-guidelines` - AI Manim code generation (stub endpoint, returns empty)

**Frontend (Non-functional UI Components):**
- `AIAssistant.tsx` - Renders UI but doesn't call working API endpoints
- `geminiService.ts` - Placeholder functions with no actual Vertex AI integration

### Configuration for Future Enablement

When ready to enable AI features in Phase 3+, set these environment variables:

```bash
# Enable AI features
ENABLE_AI_FEATURES=true

# GCP Vertex AI configuration
VERTEX_AI_PROJECT_ID=your-gcp-project-id
VERTEX_AI_LOCATION=us-central1  # or your preferred location

# Service account credentials (for GCP authentication)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### Implementation Notes

**Status of AI Components:**
- ✅ Frontend UI exists (non-functional)
- ✅ API endpoint stubs exist (return empty/default responses)
- ✅ Error handling for disabled features (graceful degradation)
- ❌ Actual Vertex AI Gemini integration (pending Phase 3)
- ❌ Backend service layer for AI operations (pending Phase 3)

**When Enabling AI Features:**
1. Implement actual `GeminiService` class in backend
2. Add Vertex AI API calls for summarization, expansion, Manim generation
3. Connect frontend `AIAssistant.tsx` to backend AI endpoints
4. Add comprehensive tests for AI operations
5. Update this documentation with implementation details

### Security Considerations

- AI feature flag (`ENABLE_AI_FEATURES`) provides safe opt-in mechanism
- GCP credentials are NOT loaded unless AI features are enabled
- Sensitive error details are logged securely (not exposed in HTTP responses)
- API endpoints return safe error messages when AI features disabled

## Database Models

**Full database schema documentation:** See `docs/sdd_database_design.md`

Key relationships:
- `Curriculum` (1) -> (N) `Node` - One curriculum has many nodes
- `Node` (1) -> (N) `NodeLink` - Nodes are connected via directed links
- `Node` (1) -> (1) `NodeContent` - Each node has associated content
- External integrations: `ZoteroItem`, `YouTubeVideo` store cached API data

**Core Tables:**
- `curriculums` - Curriculum maps (curriculum_id, title, description, is_public, timestamps)
- `nodes` - Curriculum nodes (node_id, curriculum_id, parent_node_id, title, order_index, timestamps)
- `node_contents` - Node content (content_id, node_id, markdown_content, ai fields, manim_guidelines, timestamps)
- `node_links` - External resource links (link_id, node_id, zotero_item_id, youtube_video_id, link_type, created_at)
- `zotero_items` - Cached Zotero literature (NOT currently in use)
- `youtube_videos` - Cached YouTube videos (NOT currently in use)

**Important:** All primary keys use VARCHAR(36) for UUID strings. See `docs/sdd_database_design.md` section 4 for UUID handling policy.

## Git Workflow

The frontend is a git submodule. When making changes:
1. Work in backend or frontend directories independently
2. Commit frontend changes in `MATHESIS-LAB_FRONT/`, then commit submodule reference in root
3. Recent commits focus on test infrastructure and CRUD operations

## Test-Driven Development

This project follows TDD principles:
1. Write failing test first (Red)
2. Implement minimum code to pass (Green)
3. Refactor while keeping tests green (Refactor)

Tests should cover:
- Unit level: Service methods, model validations
- Integration level: Full API request/response cycles
- Test coverage target: 80%+

### Mandatory Testing Policy

**One File = One Test File**

When creating ANY new source file, you MUST create a corresponding test file:

**Backend (Python):**
- Source: `backend/app/services/example_service.py`
- Test: `backend/tests/unit/test_example_service.py`
- Run: `pytest backend/tests/unit/test_example_service.py`

**Frontend (TypeScript/React):**
- Source: `MATHESIS-LAB_FRONT/components/ExampleComponent.tsx`
- Test: `MATHESIS-LAB_FRONT/components/ExampleComponent.test.tsx`
- Run: `npm test ExampleComponent.test.tsx`

**Test Workflow (Required):**

1. **Unit Tests FIRST** - Before any integration or E2E tests:
   ```bash
   # Backend
   pytest backend/tests/unit/test_<filename>.py -v

   # Frontend
   npm test <ComponentName>.test.tsx
   ```

2. **All unit tests must PASS** before proceeding to E2E tests

3. **E2E Tests AFTER unit tests pass:**
   ```bash
   # Backend integration tests (API E2E)
   pytest backend/tests/integration/ -v

   # Frontend E2E (when Cypress/Playwright is set up)
   npm run test:e2e
   ```

**Never skip unit tests.** If unit tests fail, fix them before moving forward. If E2E tests are needed, only run them after all unit tests pass successfully.

## Frontend Implementation Status

### ✅ Completed Features

**Services (API Client Layer):**
- ✅ `curriculumService.ts` - Full CRUD operations for curriculums
- ✅ `nodeService.ts` - Node link management (Zotero, YouTube) with proper API calls
- ✅ Link creation: `createZoteroLink()`, `createYouTubeLink()`
- ✅ Link deletion: `deleteNodeLink()`
- ✅ Link retrieval: `fetchNodeLinks()`

**Components:**
- ✅ `CurriculumEditor.tsx` - Display and manage curriculum nodes
- ✅ `NodeEditor.tsx` - Edit node content and manage linked resources
- ✅ `CreateNodeModal.tsx` - Add new nodes to curriculum
- ✅ `LinkedResourceItem` component - Display links with delete capability

**Type Definitions:**
- ✅ Core types: `Curriculum`, `Node`, `NodeContent`, `NodeLink*` interfaces

### ✅ All Issues Fixed!

**Issue 1: Type Definition Error - FIXED ✓**
- **Location:** `types.ts` Line 68
- **Status:** `links?: NodeLinkResponse[];` ✓ Correct type

**Issue 2: Zotero Link Parameter - FIXED ✓**
- **Location:** `types.ts` Line 29
- **Status:** `zotero_key: string;` ✓ Correct parameter name

**Issue 3: Node Content Property Access - FIXED ✓**
- **Location:** `CurriculumEditor.tsx` Line 108
- **Status:** `node.content?.markdown_content?.substring(0, 150)` ✓ Correct access pattern

**Issue 4 & 5: AI Service Integration - DEFERRED TO PHASE 3+**
- **Reason:** AI features are currently disabled and will be implemented in Phase 3
- **Placeholder Components:** AIAssistant.tsx and geminiService.ts exist but are non-functional stubs
- **Future Implementation:** Will refactor to call backend API endpoints when AI features are enabled

### Frontend API Integration Points

**✅ Fully Working & Tested:**
- Curriculum CRUD operations (Create, Read, Update, Delete)
- Node CRUD operations (Create, Read, Update, Delete)
- Node-to-Node link management (EXTENDS, REFERENCES relationships)
- PDF/Drive file link management
- NodeGraph visualization (Obsidian-style force-directed graph)
- E2E tests with comprehensive screenshot documentation

**⏳ Planned for Phase 3+:**
- AI summarize/expand/manim features (currently disabled)
- Vertex AI Gemini integration

## Error Handling Policy

**Critical Rule: Stop on Repeated Errors**

If the same error occurs 3 or more times consecutively during any operation (testing, building, running commands, etc.):
1. **STOP immediately** - Do not continue attempting the same approach
2. **Ask the user** - Explain the recurring error and ask for guidance
3. **Provide context** - Show what was attempted and what failed
4. **Suggest alternatives** - If possible, propose different approaches to solve the issue

This prevents infinite loops and wasted time on approaches that are not working.

**Debugging and Testing Rule: NO Try-Except During Development**

When writing test scripts or debugging code:
- **NEVER use try-except/try-catch blocks** during development
- Let errors propagate naturally so you can see the actual error messages
- Only add error handling after debugging is complete
- Use try-except only in production code, not in test/debug scripts

This ensures:
- Clear visibility of actual problems (not hidden by generic error handlers)
- Accurate stack traces for debugging
- Better understanding of what's failing and why

## Current Project Status (Latest Update)

### ✅ Working Features

**Backend:**
- All pytest tests passing (18/18)
- FastAPI server running on port 8000
- Database initialization and schema working
- CRUD operations for curriculums, nodes, content, links
- API endpoints fully functional

**Frontend:**
- React 19 + TypeScript + Vite development server on port 3002
- All frontend unit tests passing (29/29)
- Page rendering and UI components working
- Modal dialogs functioning properly

**CRUD Operations (Tested with Playwright):**
- ✅ CREATE: New curriculum creation via modal form
- ✅ READ: Curriculum list display and detail page navigation
- ✅ UPDATE: Properties panel for curriculum title/description editing
- ✅ DELETE: Delete buttons visible and functional

### 🔧 Recent Fixes

1. **Frontend Module Export Error:**
   - Issue: `geminiService.ts` importing missing `API_BASE_URL` from constants
   - Fix: Added `export const API_BASE_URL = '/api/v1';` to `constants.ts`
   - Commit: `53e09c2` (frontend), `fcf8db5` (root)

2. **Vitest Configuration:**
   - Changed pool from 'forks' to 'threads' for WSL2 compatibility
   - Added test timeout (10000ms)

3. **setupTests.ts:**
   - Updated deprecated testing-library import

4. **NodeEditor.test.tsx:**
   - Fixed React Router integration
   - Updated DOM selectors
   - Removed unimplemented modal tests

### 🚀 Ready for Production

The full application stack is now fully operational and tested:
- Backend: `python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`
- Frontend: `cd MATHESIS-LAB_FRONT && npm run dev`

Both services are running and fully connected via REST API at `/api/v1`.

### 📊 Phase 2 Completion Status

**✅ All Phase 2 Features Implemented:**
1. NodeGraph component - Obsidian-style force-directed graph visualization
2. Node-to-Node link relationships - EXTENDS, REFERENCES link types
3. PDF/Drive file link management - Full CRUD operations
4. Complete E2E test coverage - Playwright tests with screenshots
5. All unit tests passing - 29/29 frontend tests, 18/18 backend tests
6. Vite build optimization - Tree-shaking disabled to preserve all components
7. Type safety - All TypeScript interfaces properly defined and validated

---

## 📊 Test Report Generation (NEW - v1.0)

### Quick Start

Generate comprehensive test reports with metadata automatically:

```bash
# 1. Run tests
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest backend/tests/ -v

# 2. Generate report (metadata loaded automatically)
python tools/test_report_generator.py --title "My Test Report"

# 3. Open report
open test_reports/My_Test_Report__*/README.pdf
```

### What's Included

✅ **5 Metadata Sections:**
1. ⚠️ Risk Assessment & Untested Areas (5 items with severity levels)
2. 📈 Performance Benchmarking (6 metrics with before/after)
3. 📦 Deployment Notes & Dependencies (6-step checklist)
4. 🛠️ Technical Debt & Follow-ups (8 items with priority)
5. ✅ Pre-Deployment Validation (7-item checklist)

✅ **Report Formats:**
- README.md (24KB with full metadata sections)
- README.pdf (1.2MB with 25 embedded E2E screenshots)
- Screenshots directory with all test screenshots

### Metadata Management

**Current Approach (Manual):**
- Edit `tools/report_metadata.json` directly
- Include all 5 sections with project-specific data
- Commit with test report for version control

**Future Approach (LLM-Based):**
- Create `tools/generate_metadata.py` to auto-generate via Claude/GPT-4/Gemini
- LLM analyzes test results and generates JSON
- Same final report, zero manual effort

### Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `tools/test_report_generator.py` | Main report generation logic | ✅ Ready |
| `tools/report_metadata.json` | Metadata structure (5 sections) | ✅ Ready |
| `docs/REPORT_GENERATION_PIPELINE.md` | Complete pipeline guide | ✅ New |
| `docs/METADATA_GENERATION_GUIDE.md` | LLM metadata generation guide | ✅ New |
| `tools/generate_metadata.py` | LLM-based metadata generator | 📅 To implement |

### Documentation

**For detailed information, see:**
- **`docs/REPORT_GENERATION_PIPELINE.md`** - Full architecture and automation guide
- **`docs/METADATA_GENERATION_GUIDE.md`** - LLM prompt engineering and implementation
- **`docs/CI_CD_AUTOMATION.md`** - GitHub Actions integration

### Metadata Schema

**5 Core Sections in report_metadata.json:**

```json
{
  "risks_and_untested_areas": {
    "items": [
      {
        "area": "...",
        "risk_level": "high|medium|low",
        "description": "...",
        "mitigation": "..."
      }
    ]
  },
  "performance_benchmarking": {
    "items": [
      {
        "component": "...",
        "before": "...",
        "after": "...",
        "status": "✅ acceptable"
      }
    ]
  },
  "dependencies_and_deployment_notes": {
    "deployment_order": [
      {
        "step": 1,
        "required": true,
        "action": "...",
        "command": "..."
      }
    ]
  },
  "technical_debt_and_followups": {
    "items": [
      {
        "id": "TECH-001",
        "title": "...",
        "priority": "P1|P2|P3|P4",
        "estimated_effort": "...",
        "owner": "..."
      }
    ]
  },
  "validation_checklist": {
    "items": [
      {
        "item": "...",
        "status": "PASS|FAIL|PENDING",
        "date": "YYYY-MM-DD"
      }
    ]
  }
}
```

### Next Steps

**Phase 1 (Current):** Manual metadata creation ✅
**Phase 2:** Implement `generate_metadata.py` with Claude API
**Phase 3:** Support GPT-4 and Gemini models
**Phase 4:** Full GitHub Actions automation
**Phase 5:** Web UI for metadata editing

### Key Implementation Notes

- Metadata is **independent of test execution** - can be updated separately
- Reports work **with any LLM** that can output valid JSON
- **Schema is versioned** in the JSON file for forward compatibility
- All metadata is **human-readable and editable** in the JSON file
- PDF generation **automatically embeds 25+ E2E screenshots**
