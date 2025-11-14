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

## Common Commands

### Backend Development

**Run the development server:**
```bash
cd backend
python -m backend.app.main
# Or: uvicorn backend.app.main:app --reload
```

**Run tests:**
```bash
# All tests
pytest

# Unit tests only
pytest backend/tests/unit/

# Integration tests only
pytest backend/tests/integration/

# Specific test file
pytest backend/tests/integration/test_curriculum_crud_api.py

# With verbose output
pytest -v

# With coverage
pytest --cov=backend/app
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

**Note:** Frontend requires `GEMINI_API_KEY` in `.env.local` file.

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

## Database Models

Key relationships:
- `Curriculum` (1) -> (N) `Node` - One curriculum has many nodes
- `Node` (1) -> (N) `NodeLink` - Nodes are connected via directed links
- `Node` (1) -> (1) `NodeContent` - Each node has associated content
- External integrations: `ZoteroItem`, `YouTubeVideo` store cached API data

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

## Error Handling Policy

**Critical Rule: Stop on Repeated Errors**

If the same error occurs 3 or more times consecutively during any operation (testing, building, running commands, etc.):
1. **STOP immediately** - Do not continue attempting the same approach
2. **Ask the user** - Explain the recurring error and ask for guidance
3. **Provide context** - Show what was attempted and what failed
4. **Suggest alternatives** - If possible, propose different approaches to solve the issue

This prevents infinite loops and wasted time on approaches that are not working.
